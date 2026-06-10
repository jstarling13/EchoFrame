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
from products import get_product

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
    session_id: str = Form(...),
    product:    str = Form("clarity", max_length=64),
    tier:       str = Form("", max_length=32),
    industry:   str = Form("", max_length=200),   # Clarity-only; ignored by other products
    location:   str = Form("", max_length=200),   # Clarity-only; ignored by other products
    file: UploadFile = File(...),
):
    # 0 — resolve which report product to run (defaults to flagship Clarity)
    selected = get_product(product)
    resolved_tier = selected.resolve_tier(tier)

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
    fields = {"industry": industry, "location": location, "tier": resolved_tier}

    async def run_report():
        try:
            selected.generate(email, customer_name, fields)
        except Exception:
            print(f"[EchoFrame] REPORT ERROR ({selected.slug}):\n{traceback.format_exc()}", flush=True)

    background_tasks.add_task(run_report)
    tier_note = f" tier='{resolved_tier}'" if resolved_tier else ""
    print(f"[EchoFrame] Dispatched product='{selected.slug}'{tier_note}.")
    return JSONResponse({
        "status": "ok",
        "message": "Report generation started.",
        "product": selected.slug,
        "tier": resolved_tier,
    })


# ----- Revenue Suite: three-file intake (Call Catch + Quote Revive + Clear Ledger) -----

@app.get("/upload/revenue-suite")
async def revenue_suite_page(request: Request, email: str = "", session_id: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="intake_revenue_suite.html",
        context={"email": email, "session_id": session_id},
    )


async def _read_validated_csv(file: UploadFile, label: str) -> bytes:
    """Validate one uploaded CSV (extension, content-type, size, UTF-8) and return its bytes."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail=f"{label}: only .csv files are accepted.")
    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct and ct not in ALLOWED_CSV_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"{label}: invalid content type.")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{label}: file too large (max 5 MB).")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail=f"{label}: file must be UTF-8 encoded text.")
    return raw


@app.post("/api/upload-revenue-suite")
@limiter.limit("5/minute")
async def upload_revenue_suite(
    request: Request,
    background_tasks: BackgroundTasks,
    email:      str = Form(...),
    session_id: str = Form(...),
    callcatch:   UploadFile = File(...),
    quoterevive: UploadFile = File(...),
    clearledger: UploadFile = File(...),
):
    selected = get_product("revenue-suite")

    # validate & verify payment before accepting any file
    email = _validate_email(email)
    _verify_stripe_session(session_id, email)

    # validate all three, then write all three (engine reads <email>_<part>.csv)
    cc_bytes = await _read_validated_csv(callcatch,   "Call Catch log")
    qr_bytes = await _read_validated_csv(quoterevive, "Quote Revive export")
    cl_bytes = await _read_validated_csv(clearledger, "Clear Ledger export")

    UPLOADS_DIR.mkdir(exist_ok=True)
    stem = _safe_email(email)
    (UPLOADS_DIR / f"{stem}_callcatch.csv").write_bytes(cc_bytes)
    (UPLOADS_DIR / f"{stem}_quoterevive.csv").write_bytes(qr_bytes)
    (UPLOADS_DIR / f"{stem}_clearledger.csv").write_bytes(cl_bytes)
    print("[EchoFrame] Revenue Suite - 3 CSVs received and saved.")

    customer_name = _load_customer_name(email)

    async def run_report():
        try:
            selected.generate(email, customer_name, {})
        except Exception:
            print(f"[EchoFrame] REPORT ERROR (revenue-suite):\n{traceback.format_exc()}", flush=True)

    background_tasks.add_task(run_report)
    print("[EchoFrame] Dispatched product='revenue-suite'.")
    return JSONResponse({
        "status": "ok",
        "message": "Report generation started.",
        "product": selected.slug,
    })


# ----- Stripe webhook -----------------------------------------------------------

# Hard ceiling on webhook body size; oversized payloads are rejected, never parsed.
MAX_WEBHOOK_BYTES = 1 * 1024 * 1024  # 1 MB


@app.post("/webhook/stripe")
@limiter.limit("60/minute")
async def stripe_webhook(request: Request):
    payload = await request.body()
    if len(payload) > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=400, detail="Webhook payload too large.")

    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature.")

    # Verify authenticity & integrity. construct_event also enforces Stripe's
    # 300-second timestamp tolerance (rejects replayed/stale signatures) and
    # raises on malformed JSON or a bad signature.
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload.")

    event_id = (event or {}).get("id") or ""

    # Idempotency: Stripe retries deliver the same event id; process each once.
    if event_id and event_id in _processed_webhook_events:
        return JSONResponse({"status": "ok", "note": "duplicate"})
    if event_id:
        _mark_event_processed(event_id)

    # Only act on completed checkouts. Save the buyer's email + name so the
    # Step-2 upload page can attribute the report. Product routing happens at
    # upload time via the per-product intake page (the `product` form field).
    if (event or {}).get("type") == "checkout.session.completed":
        session = ((event.get("data") or {}).get("object")) or {}
        details = session.get("customer_details") or {}
        email = (details.get("email") or "").strip().lower()
        name  = (details.get("name") or "").strip() or "Client"
        if email:
            try:
                _save_customer(email, name)
                print(f"[EchoFrame] Checkout complete - saved customer {email}.")
            except Exception:
                print(f"[EchoFrame] WEBHOOK ERROR saving customer:\n{traceback.format_exc()}", flush=True)

    return JSONResponse({"status": "ok"})
