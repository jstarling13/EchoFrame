import os
import re
import json
import stripe
import traceback
from collections import OrderedDict
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from engine import generate_clarity_report

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parent
UPLOADS_DIR   = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

_REQUIRED_ENV_VARS = (
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "ANTHROPIC_API_KEY",   # required by engine.py for Claude narrative generation
    "RESEND_API_KEY",      # required by engine.py for email delivery
)
_missing = [k for k in _REQUIRED_ENV_VARS if not os.environ.get(k)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB hard ceiling

_EMAIL_RE      = re.compile(r'^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,}$')
# Dots are intentionally excluded — prevents ".." from surviving into filenames
_SAFE_CHAR_RE  = re.compile(r'[^a-zA-Z0-9_+\-]')

# In-memory idempotency store — bounded OrderedDict used as an ordered set.
# Max 10,000 entries; oldest are evicted when the cap is reached.
# PRODUCTION NOTE: Replace with Redis (SETNX with TTL) for multi-process deployments.
#   State is lost on restart, which allows replay of Stripe retries issued before restart.
_MAX_IDEMPOTENCY_ENTRIES = 10_000
_processed_webhook_events: OrderedDict[str, None] = OrderedDict()


def _mark_event_processed(event_id: str) -> None:
    """Record event_id as processed; evict oldest entry if cap is reached."""
    if event_id in _processed_webhook_events:
        return
    _processed_webhook_events[event_id] = None
    if len(_processed_webhook_events) > _MAX_IDEMPOTENCY_ENTRIES:
        _processed_webhook_events.popitem(last=False)  # evict oldest

# ── App ───────────────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)
app     = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-src 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]   = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Referrer-Policy"]            = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]         = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"]    = _CSP_POLICY
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_email(email: str) -> str:
    """Validate and normalise email; raise 400 on bad format."""
    email = email.strip().lower()
    if not email or len(email) > 320:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email address.")
    return email


def _safe_email(email: str) -> str:
    """Return a filesystem-safe stem — strict allowlist, prevents path traversal."""
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', local)}_at_{_SAFE_CHAR_RE.sub('_', domain)}"


def _sidecar_path(email: str) -> Path:
    return UPLOADS_DIR / f"{_safe_email(email)}.json"


def _save_customer(email: str, name: str) -> None:
    UPLOADS_DIR.mkdir(exist_ok=True)
    _sidecar_path(email).write_text(
        json.dumps({"email": email, "name": name}), encoding="utf-8"
    )


def _load_customer_name(email: str) -> str:
    try:
        data = json.loads(_sidecar_path(email).read_text(encoding="utf-8"))
        return data.get("name", "").strip() or "Client"
    except Exception:
        return "Client"


def _verify_stripe_session(session_id: str, email: str) -> None:
    """Confirm that session_id is a completed Stripe Checkout for this email.

    Raises HTTPException on any verification failure.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=403, detail="Invalid or expired session.")
    except stripe.error.StripeError:
        raise HTTPException(status_code=503, detail="Payment verification unavailable.")

    if session.get("status") != "complete":
        raise HTTPException(status_code=403, detail="Payment not completed for this session.")

    session_email = (
        (session.get("customer_details") or {}).get("email") or ""
    ).lower().strip()
    if session_email and session_email != email:
        raise HTTPException(status_code=403, detail="Email does not match payment record.")


# ── Drop zone UI ──────────────────────────────────────────────────────────────

@app.get("/upload")
async def upload_page(request: Request, email: str = "", session_id: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"email": email, "session_id": session_id},
    )


# ── CSV intake + report trigger ───────────────────────────────────────────────

ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "text/plain",
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
}


@app.post("/api/upload")
@limiter.limit("5/minute")
async def upload_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    email:      str = Form(...),
    industry:   str = Form(..., max_length=200),
    location:   str = Form(..., max_length=200),
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    # 1 — validate & normalise email
    email = _validate_email(email)

    # 2 — verify completed Stripe payment before accepting any file
    _verify_stripe_session(session_id, email)

    # 3 — filename extension check
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    # 4 — content-type check (browsers send this; do not rely on it alone)
    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct and ct not in ALLOWED_CSV_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type.")

    # 5 — read with size ceiling; +1 byte to detect oversized payloads
    raw_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5 MB.")

    # 6 — must decode as UTF-8 text (rejects binary uploads)
    try:
        raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    UPLOADS_DIR.mkdir(exist_ok=True)
    dest = UPLOADS_DIR / f"{_safe_email(email)}.csv"
    dest.write_bytes(raw_bytes)
    print("[EchoFrame] CSV upload received and saved.")

    customer_name = _load_customer_name(email)

    async def run_report():
        try:
            generate_clarity_report(email, customer_name, industry, location)
        except Exception:
            print(f"[EchoFrame] REPORT ERROR:\n{traceback.format_exc()}", flush=True)

    background_tasks.add_task(run_report)
    return JSONResponse({"status": "ok", "message": "Report generation started."})


# ── Stripe webhook ────────────────────────────────────────────────────────────

@app.post("/webhook/stripe")
@limiter.limit("60/minute")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed payload")

    event_id = event.get("id", "")

    # Idempotency guard — skip already-processed events (Stripe retries).
    # Uses bounded OrderedDict; see _mark_event_processed for eviction policy.
    if event_id and event_id in _processed_webhook_events:
        return JSONResponse({"status": "ok", "note": "duplicate"})

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if hasattr(session, "to_dict"):
            session = session.to_dict()

        details = session.get("customer_details") or {}
        email   = (details.get("email") or "").strip().lower()
        name    = (details.get("name") or "").strip() or "Client"

        print("[EchoFrame] Payment event processed.")  # no PII in logs

        if email:
            try:
                _save_customer(email, name)
            except Exception:
                print(f"[EchoFrame] WARNING: customer metadata save failed.\n{traceback.format_exc()}")

    if event_id:
        _mark_event_processed(event_id)

    return JSONResponse({"status": "ok"})
