import os
import re
import json
import time
import stripe
import traceback
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlencode
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from registry import get_product, route_stripe_purchase
from intake_specs import INTAKE_SPECS, build_context

import store
import sign
import emails
import email_failsafe
import review_gate
from reminders import run_reminders

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# App-wide safety net: if any product engine's report delivery fails (unverified
# domain, mistyped client address, bounce, Resend outage), the report is routed
# to the owner's inbox instead of being silently lost. Touches no engine code.
email_failsafe.install()

# Human-review gate: every customer-bound REPORT is held and emailed to the owner
# for one-click approval before it reaches the customer — making the advertised
# "a real analyst reviews every report" literally true. Installed AFTER the
# fail-safe so the review copies are themselves fail-safe protected.
#
# THE ONE LEVER FOR FULL AUTONOMY: set env REVIEW_MODE=off to disable the gate
# and return to instant auto-send (planned once enough customer data has proven
# the reports out — e.g. before going on active duty).
review_gate.install()

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parent
# UPLOADS_DIR is a WRITE path, so on serverless it must point at the only writable
# location (/tmp) via ECHOFRAME_UPLOADS_DIR. Locally it defaults to ./uploads,
# matching the report engines (which honour the same env var). Bundled read-only
# assets (templates, samples, logos, benchmarks) are NOT redirected.
UPLOADS_DIR   = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR / "uploads")
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

# Recommended for the recurring-renewal loop. NOT hard-required at import so the
# month-1 checkout flow still boots before these are configured — they're checked
# where used (renewal webhook / link building) and warned about at startup.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")
_RECOMMENDED_ENV_VARS = ("SIGNING_SECRET", "PUBLIC_BASE_URL")
_rec_missing = [k for k in _RECOMMENDED_ENV_VARS if not os.environ.get(k)]
if _rec_missing:
    print(f"[EchoFrame] WARNING: recurring-renewal env vars not set: {', '.join(_rec_missing)}. "
          f"Month-1 signup still works; renewal upload links will be disabled until these are set.")
if not store.is_configured():
    print("[EchoFrame] WARNING: no durable store (Upstash Redis) configured — "
          "using in-memory fallback. Set KV_REST_API_URL/KV_REST_API_TOKEN in production.")

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
    "script-src 'self' 'unsafe-inline'; "
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


def _save_customer(email: str, name: str, **extra) -> None:
    """Persist the buyer's name (+ any extra metadata) for later attribution.

    Writes the local sidecar JSON (unchanged; used by the month-1 flow and tests)
    AND mirrors to the durable store so the data survives serverless invocations,
    where the local /tmp sidecar does not persist between the webhook and upload.
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    _sidecar_path(email).write_text(
        json.dumps({"email": email, "name": name}), encoding="utf-8"
    )
    try:
        store.save_customer_record(_safe_email(email), {"email": email, "name": name, **extra})
    except Exception:
        # Durable mirror is best-effort; never fail the webhook over it.
        print(f"[EchoFrame] WARN: durable customer mirror failed:\n{traceback.format_exc()}", flush=True)


def _load_customer_name(email: str) -> str:
    # Prefer the local sidecar (month-1 / tests); fall back to the durable store
    # (renewals on serverless, where the sidecar was written in another invocation).
    try:
        data = json.loads(_sidecar_path(email).read_text(encoding="utf-8"))
        name = data.get("name", "").strip()
        if name:
            return name
    except Exception:
        pass
    try:
        rec = store.load_customer_record(_safe_email(email))
        if rec and (rec.get("name", "") or "").strip():
            return rec["name"].strip()
    except Exception:
        pass
    return "Client"


def _claim_event(event_id: str) -> bool:
    """Idempotency gate. Returns True if this event is being seen for the first
    time (caller should process it), False if it's a Stripe retry/duplicate.

    Uses the durable store's atomic SETNX+TTL when configured; otherwise falls
    back to the bounded in-memory OrderedDict (dev / single-process / tests)."""
    if not event_id:
        return True
    if store.is_configured():
        try:
            return store.claim_event(event_id)
        except Exception:
            print(f"[EchoFrame] WARN: durable idempotency failed, using memory:\n{traceback.format_exc()}", flush=True)
    if event_id in _processed_webhook_events:
        return False
    _mark_event_processed(event_id)
    return True


# Vercel sets the VERCEL env var inside every serverless invocation.
IS_SERVERLESS = bool(os.environ.get("VERCEL"))


def _run_report_sync(generate, email: str, name: str, fields: dict, slug: str) -> None:
    try:
        generate(email, name, fields)
    except Exception:
        print(f"[EchoFrame] REPORT ERROR ({slug}):\n{traceback.format_exc()}", flush=True)


async def _dispatch_report(background_tasks: BackgroundTasks, selected, email: str,
                           name: str, fields: dict) -> None:
    """Run report generation.

    On serverless (Vercel) a FastAPI BackgroundTask is NOT guaranteed to run once
    the response has been sent — the function can be frozen/terminated. So we
    generate INLINE there (off the event loop via a threadpool); vercel.json's
    maxDuration provides the headroom for the Claude call. Locally we keep the
    original fire-after-response background behaviour for a snappy upload UX.
    """
    if IS_SERVERLESS:
        await run_in_threadpool(_run_report_sync, selected.generate, email, name, fields, selected.slug)
    else:
        background_tasks.add_task(_run_report_sync, selected.generate, email, name, fields, selected.slug)


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

    if getattr(session, "status", None) != "complete":
        raise HTTPException(status_code=403, detail="Payment not completed for this session.")

    _cd = getattr(session, "customer_details", None)
    session_email = (getattr(_cd, "email", None) or "").lower().strip()
    if session_email and session_email != email:
        raise HTTPException(status_code=403, detail="Email does not match payment record.")


def _sget(obj, key, default=None):
    """Read a field whether obj is a plain dict or a Stripe SDK object.

    Stripe objects in this SDK version don't expose a dict-style .get(), so a
    bare obj.get(key) raises. This works for both shapes.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_plain(obj):
    """Convert a Stripe SDK object into a plain (recursive) dict so downstream
    code that relies on dict.get() keeps working. Returns {} on failure."""
    if obj is None or isinstance(obj, dict):
        return obj or {}
    for attr in ("to_dict_recursive", "to_dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    try:
        return json.loads(str(obj))
    except Exception:
        return {}


def _resolve_session(session_id: str) -> dict:
    """Best-effort: pull buyer email + purchased product/tier off a Checkout session.

    Stripe only substitutes {CHECKOUT_SESSION_ID} into Payment Link redirect URLs
    (never the email or product), so the upload page resolves them itself:
      - email   from session.customer_details.email
      - product from the purchased line item, via registry.route_stripe_purchase
                (matches by live Stripe product id, falling back to product name —
                 which is what makes sandbox/test clones route correctly too).
    Returns {"email", "product", "tier"}; blanks on any failure (never raises).
    """
    out = {"email": "", "product": "", "tier": ""}
    if not session_id:
        return out
    try:
        session = stripe.checkout.Session.retrieve(
            session_id, expand=["line_items.data.price.product"]
        )
    except Exception:
        return out
    # NOTE: Stripe SDK objects don't expose a dict-style .get() here — use
    # attribute access (getattr) throughout.
    try:
        cd = getattr(session, "customer_details", None)
        out["email"] = (getattr(cd, "email", None) or "").strip().lower()
    except Exception:
        pass
    try:
        li = getattr(session, "line_items", None)
        data = getattr(li, "data", None) or []
        if data:
            price = getattr(data[0], "price", None)
            prod  = getattr(price, "product", None) if price else None
            if isinstance(prod, str):
                pid, pname = prod, ""
            else:
                pid   = getattr(prod, "id", "") or ""
                pname = getattr(prod, "name", "") or ""
            routed = route_stripe_purchase(product_id=pid, product_name=pname)
            if routed.get("slug"):
                out["product"] = routed["slug"]
                out["tier"]    = routed.get("tier") or ""
    except Exception:
        pass
    return out


# ── Drop zone UI ──────────────────────────────────────────────────────────────

@app.get("/upload")
async def upload_page(
    request: Request,
    email: str = "",
    session_id: str = "",
    token: str = "",
    product: str = "",
    tier: str = "",
):
    # Unresolved Stripe template variables (e.g. "{CHECKOUT_SESSION_CUSTOMER_EMAIL}")
    # are not real values — treat them as missing.
    if "{" in email:
        email = ""
    if "{" in product:
        product = ""

    # If we arrived with a session_id but are missing the email or the product,
    # resolve both from the Stripe session and re-enter with clean query params so
    # the buyer lands on the correct intake page with their email pre-filled.
    if session_id and (not email or not product):
        info = _resolve_session(session_id)
        new_email   = email   or info["email"]
        new_product = product or info["product"]
        new_tier    = tier    or info["tier"]
        if (new_email, new_product, new_tier) != (email, product, tier):
            params = {"session_id": session_id}
            if new_email:   params["email"]   = new_email
            if token:       params["token"]   = token
            if new_product: params["product"] = new_product
            if new_tier:    params["tier"]    = new_tier
            return RedirectResponse(url=f"/upload?{urlencode(params)}", status_code=303)
    # Renewal links carry a product (+ optional tier) so the client lands on the
    # exact intake page for THAT subscription's report. Month-1 (no product) keeps
    # the original generic Clarity upload page untouched.
    if product and product in INTAKE_SPECS:
        prod = get_product(product)
        resolved_tier = prod.resolve_tier(tier)
        tier_label = resolved_tier.capitalize() if resolved_tier else ""
        context = build_context(product, resolved_tier, tier_label)
        context.update({"email": email, "session_id": session_id, "token": token})
        return templates.TemplateResponse(request=request, name="intake.html", context=context)

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"email": email, "session_id": session_id, "token": token},
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
    session_id: str = Form(""),                    # month-1 Stripe Checkout session
    token:      str = Form("", max_length=512),    # renewal upload token (alt to session_id)
    product:    str = Form("clarity", max_length=64),
    tier:       str = Form("", max_length=32),
    industry:   str = Form("", max_length=200),   # Clarity-only; ignored by other products
    location:   str = Form("", max_length=200),   # Clarity-only; ignored by other products
    file: UploadFile = File(...),
):
    # 1 — validate & normalise email
    email = _validate_email(email)

    # 2 — authorise: a signed renewal token OR a completed Stripe Checkout session.
    #     A valid token is authoritative for product + tier (both are signed), so a
    #     client cannot swap the product they were billed for. Neither present → 422.
    token_payload = None
    if token:
        token_payload = sign.verify_token(token)
        if not token_payload or token_payload.get("email") != email:
            raise HTTPException(status_code=403, detail="Invalid or expired upload link.")
        product = token_payload.get("product") or product
        tier    = token_payload.get("tier") or tier
    elif session_id:
        _verify_stripe_session(session_id, email)
    else:
        raise HTTPException(status_code=422, detail="Missing payment session or upload token.")

    # 0 — resolve which report product to run (defaults to flagship Clarity)
    selected = get_product(product)
    resolved_tier = selected.resolve_tier(tier)

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

    # Personalize from the typed intake fields. Every engine reads its
    # Business Name / Month / Industry / Location / Role from leading "_Key,value"
    # rows in the CSV — so inject whatever the customer typed on the page as those
    # rows. One place, personalizes the report for ALL products. (If the customer's
    # own CSV already carries "_" rows, those win — they appear later in the file.)
    try:
        _form = await request.form()
        _FORM_TO_META = {
            "business": "Business Name", "month": "Month", "industry": "Industry",
            "location": "Location", "role": "Role",
        }
        _meta_lines = []
        for _fname, _metakey in _FORM_TO_META.items():
            _val = _form.get(_fname)
            if isinstance(_val, str) and _val.strip():
                _v = _val.strip()
                if ("," in _v) or ('"' in _v) or ("\n" in _v):
                    _v = '"' + _v.replace('"', '""') + '"'
                _meta_lines.append(f"_{_metakey},{_v}")
        if _meta_lines:
            raw_bytes = ("\n".join(_meta_lines) + "\n").encode("utf-8") + raw_bytes
    except Exception:
        print(f"[EchoFrame] WARN: intake-field injection failed:\n{traceback.format_exc()}", flush=True)

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{_safe_email(email)}.csv"
    dest.write_bytes(raw_bytes)
    print("[EchoFrame] CSV upload received and saved.")

    # Renewal upload: the files are in hand, so clear this period's pending state
    # immediately — the reminder cron must not fire even if generation later fails.
    if token_payload:
        try:
            store.mark_period_uploaded(_safe_email(email), token_payload.get("period", ""))
        except Exception:
            print(f"[EchoFrame] WARN: mark_period_uploaded failed:\n{traceback.format_exc()}", flush=True)

    customer_name = _load_customer_name(email)
    fields = {"industry": industry, "location": location, "tier": resolved_tier}

    await _dispatch_report(background_tasks, selected, email, customer_name, fields)
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
async def revenue_suite_page(request: Request, email: str = "", session_id: str = "", token: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="intake_revenue_suite.html",
        context={"email": email, "session_id": session_id, "token": token},
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
    session_id: str = Form(""),                    # month-1 Stripe Checkout session
    token:      str = Form("", max_length=512),    # renewal upload token (alt to session_id)
    callcatch:   UploadFile = File(...),
    quoterevive: UploadFile = File(...),
    clearledger: UploadFile = File(...),
):
    selected = get_product("revenue-suite")

    # validate email, then authorise via renewal token OR Stripe session
    email = _validate_email(email)
    token_payload = None
    if token:
        token_payload = sign.verify_token(token)
        if not token_payload or token_payload.get("email") != email \
                or token_payload.get("product") != "revenue-suite":
            raise HTTPException(status_code=403, detail="Invalid or expired upload link.")
    elif session_id:
        _verify_stripe_session(session_id, email)
    else:
        raise HTTPException(status_code=422, detail="Missing payment session or upload token.")

    # validate all three, then write all three (engine reads <email>_<part>.csv)
    cc_bytes = await _read_validated_csv(callcatch,   "Call Catch log")
    qr_bytes = await _read_validated_csv(quoterevive, "Quote Revive export")
    cl_bytes = await _read_validated_csv(clearledger, "Clear Ledger export")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    stem = _safe_email(email)
    (UPLOADS_DIR / f"{stem}_callcatch.csv").write_bytes(cc_bytes)
    (UPLOADS_DIR / f"{stem}_quoterevive.csv").write_bytes(qr_bytes)
    (UPLOADS_DIR / f"{stem}_clearledger.csv").write_bytes(cl_bytes)
    print("[EchoFrame] Revenue Suite - 3 CSVs received and saved.")

    if token_payload:
        try:
            store.mark_period_uploaded(stem, token_payload.get("period", ""))
        except Exception:
            print(f"[EchoFrame] WARN: mark_period_uploaded failed:\n{traceback.format_exc()}", flush=True)

    customer_name = _load_customer_name(email)

    await _dispatch_report(background_tasks, selected, email, customer_name, {})
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

    event_id = _sget(event, "id") or ""

    # Idempotency: Stripe retries deliver the same event id; process each once.
    # _claim_event uses the durable store (atomic SETNX+TTL) when configured,
    # falling back to the bounded in-memory set otherwise.
    if not _claim_event(event_id):
        return JSONResponse({"status": "ok", "note": "duplicate"})

    event_type = _sget(event, "type")

    # Month-1 signup: save the buyer's email + name so the Step-2 upload page can
    # attribute the report. Product routing happens at upload time via the
    # per-product intake page (the `product` form field).
    if event_type == "checkout.session.completed":
        session = _sget(_sget(event, "data"), "object")
        details = _sget(session, "customer_details")
        email = (_sget(details, "email") or "").strip().lower()
        name  = (_sget(details, "name") or "").strip() or "Client"
        customer_id = _sget(session, "customer") or ""
        if email:
            try:
                _save_customer(email, name, stripe_customer=customer_id)
                print(f"[EchoFrame] Checkout complete - saved customer {email}.")
            except Exception:
                print(f"[EchoFrame] WEBHOOK ERROR saving customer:\n{traceback.format_exc()}", flush=True)

    # Monthly renewal: a subscription invoice was paid. Act ONLY on the recurring
    # cycle — the very first invoice (billing_reason == 'subscription_create') is
    # already covered by the checkout flow above, so we must not double-send.
    elif event_type == "invoice.payment_succeeded":
        try:
            _handle_invoice_paid(_to_plain(_sget(_sget(event, "data"), "object")))
        except Exception:
            print(f"[EchoFrame] WEBHOOK ERROR handling invoice:\n{traceback.format_exc()}", flush=True)

    return JSONResponse({"status": "ok"})


# ----- Renewal invoice handling -------------------------------------------------

def _invoice_period(invoice: dict) -> tuple[str, str]:
    """Derive (period_key, period_label) for a subscription invoice.

    Prefers the subscription line's service period; falls back to the invoice
    period, then to now. period_key is 'YYYY-MM' (one billing cycle/month);
    period_label is human-friendly, e.g. 'June 2026'.
    """
    ts = 0
    lines = ((invoice.get("lines") or {}).get("data")) or []
    if lines:
        ts = ((lines[0].get("period") or {}).get("start")) or 0
    ts = ts or invoice.get("period_start") or invoice.get("created") or 0
    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts else datetime.now(timezone.utc)
    return dt.strftime("%Y-%m"), dt.strftime("%B %Y")


def _invoice_product_id(invoice: dict) -> str:
    """Best-effort extraction of the Stripe product id from a subscription invoice,
    across a couple of API shapes."""
    lines = ((invoice.get("lines") or {}).get("data")) or []
    if not lines:
        return ""
    line = lines[0]
    price = line.get("price") or {}
    prod = price.get("product")
    if not prod:
        plan = line.get("plan") or {}
        prod = plan.get("product")
    if not prod:
        pricing = line.get("pricing") or {}
        prod = ((pricing.get("price_details") or {}).get("product")) or ""
    return prod or ""


def _resolve_invoice_email_name(invoice: dict) -> tuple[str, str]:
    """Resolve client email + name from the invoice, falling back to a Stripe
    Customer lookup and to the durable customer record."""
    email = (invoice.get("customer_email") or "").strip().lower()
    name  = (invoice.get("customer_name") or "").strip()
    customer_id = invoice.get("customer") or ""

    if (not email or not name) and customer_id:
        try:
            cust = stripe.Customer.retrieve(customer_id)
            email = email or (cust.get("email") or "").strip().lower()
            name  = name or (cust.get("name") or "").strip()
        except Exception:
            print(f"[EchoFrame] WARN: Stripe customer lookup failed:\n{traceback.format_exc()}", flush=True)

    if email and not name:
        rec = store.load_customer_record(_safe_email(email))
        if rec:
            name = (rec.get("name") or "").strip()

    return email, (name or "Client")


def _handle_invoice_paid(invoice: dict) -> None:
    """Renewal fulfilment: email the client a signed upload link for this cycle and
    record the billing period so the reminder cron can chase a missing upload."""
    billing_reason = invoice.get("billing_reason") or ""
    if billing_reason != "subscription_cycle":
        # First invoice (subscription_create) and one-off/manual invoices are not
        # recurring renewals — the checkout flow handles month-1.
        print(f"[EchoFrame] Invoice ignored (billing_reason={billing_reason!r}).")
        return

    if not os.environ.get("SIGNING_SECRET") or not PUBLIC_BASE_URL:
        print("[EchoFrame] WEBHOOK WARN: SIGNING_SECRET/PUBLIC_BASE_URL unset — "
              "cannot send renewal upload link. Set them in the environment.")
        return

    email, name = _resolve_invoice_email_name(invoice)
    if not email:
        print("[EchoFrame] WEBHOOK WARN: renewal invoice had no resolvable email.")
        return

    # Route the subscription's Stripe product to one of our report products.
    routed = route_stripe_purchase(product_id=_invoice_product_id(invoice))
    if not routed.get("product"):
        # Never guess — flag for manual review rather than send a wrong report link.
        print(f"[EchoFrame] WEBHOOK FLAG: {routed.get('flag')}")
        return

    slug = routed["slug"]
    tier = routed.get("tier") or ""
    period_key, period_label = _invoice_period(invoice)
    label = routed["product"].label

    token = sign.make_token(email, slug, tier, period_key)
    url   = sign.build_upload_url(PUBLIC_BASE_URL, email, slug, tier, token)

    # Persist customer + period state, then email the link.
    safe = _safe_email(email)
    _save_customer(email, name, stripe_customer=(invoice.get("customer") or ""))
    store.mark_period_billed(safe, period_key, {
        "email": email, "name": name, "product": slug, "tier": tier,
        "period": period_key, "period_label": period_label,
        "billed_at": int(time.time()), "uploaded": False, "reminded": False,
    })
    emails.send_upload_link(email, name, label, url, period_label=period_label)
    print(f"[EchoFrame] Renewal link sent (product={slug}, period={period_key}).")  # no PII


# ----- Reminder / safety-net cron ----------------------------------------------

@app.get("/api/cron/reminders")
async def cron_reminders(request: Request):
    """Daily safety-net job (Vercel Cron). Re-sends the upload link to any client
    billed >4 days ago who hasn't uploaded, and alerts the owner.

    Protected by CRON_SECRET: when set, Vercel Cron sends it as a Bearer token.
    """
    secret = os.environ.get("CRON_SECRET", "")
    if secret:
        if request.headers.get("authorization", "") != f"Bearer {secret}":
            raise HTTPException(status_code=401, detail="Unauthorized.")
    summary = await run_in_threadpool(run_reminders)
    return JSONResponse({"status": "ok", **summary})


# ----- Human review gate (approve / hold a held report) ------------------------

def _review_page(title: str, message: str, tone: str = "ok") -> str:
    accent = "#0a274f" if tone == "ok" else "#b91c1c"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>EchoFrame review</title></head>"
        "<body style='margin:0;background:#0a274f;font:16px system-ui;'>"
        "<div style='max-width:520px;margin:14vh auto;background:#fff;border-radius:16px;"
        "padding:40px 36px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.35)'>"
        f"<div style='font:700 22px system-ui;color:{accent};margin-bottom:10px'>{title}</div>"
        f"<div style='color:#374151;line-height:1.5'>{message}</div>"
        "<div style='color:#9ca3af;font-size:12px;margin-top:22px'>EchoFrame</div>"
        "</div></body></html>"
    )


@app.get("/api/review/approve")
async def review_approve(id: str, t: str, delay: int = 0):
    """One-click approval link from the owner's review email. Releases the held
    report to the real customer — immediately by default, or scheduled `delay`
    minutes out (also honours the REVIEW_SEND_DELAY_MINUTES env default)."""
    rec = review_gate.peek(id)
    if not rec or rec.get("token") != t:
        raise HTTPException(status_code=404, detail="Review not found or link expired.")
    if rec.get("status") == "approved":
        return HTMLResponse(_review_page(
            "Already sent",
            f"This report was already delivered to <strong>{rec.get('to','the customer')}</strong>.",
        ))
    if rec.get("status") == "held":
        return HTMLResponse(_review_page(
            "On hold",
            "This report was marked held. Edit and resend it manually when ready.",
        ))
    delay_minutes = delay if delay and delay > 0 else None
    await run_in_threadpool(review_gate.release, id, delay_minutes)
    to_label = rec.get("to", "the customer")
    eff = delay_minutes if delay_minutes is not None else review_gate._default_delay_minutes()
    if eff and eff > 0:
        msg = f"Report approved — <strong>scheduled to send to {to_label} in {eff} min</strong>."
    else:
        msg = f"Report approved and delivered to <strong>{to_label}</strong>."
    return HTMLResponse(_review_page("Sent ✓", msg))


@app.get("/api/review/hold")
async def review_hold(id: str, t: str):
    """Mark a held report as held (owner will edit / resend manually)."""
    rec = review_gate.peek(id)
    if not rec or rec.get("token") != t:
        raise HTTPException(status_code=404, detail="Review not found or link expired.")
    review_gate.hold(id)
    return HTMLResponse(_review_page(
        "Held",
        "Marked held — nothing was sent to the customer. Edit and resend manually.",
    ))


# ----- Self-test: prove the review gate on the LIVE server ---------------------
# Token-guarded and hard-wired to email only the owner's own inbox, so it can
# never be abused to send mail anywhere else. Creates a real held sample report
# ON this server, so the Approve button in the resulting email actually works.
_SELFTEST_KEY = "echoframe-selftest-9f3a7c12e8b54d6a"
_SELFTEST_CUSTOMER = "jacobstarling4313+client@gmail.com"  # a +alias of the owner

@app.get("/api/review/selftest")
async def review_selftest(request: Request, key: str = ""):
    if key != _SELFTEST_KEY:
        raise HTTPException(status_code=404, detail="Not found.")
    import base64, resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    # Point the Approve/Hold links back at whatever host this request came in on,
    # so the button always reaches this same server.
    review_gate.set_base_url(str(request.base_url))
    report_html = (
        "<!doctype html><h1 style='color:#0a274f;font-family:system-ui'>EchoFrame — Monthly Clarity Report</h1>"
        "<p style='font-family:system-ui'>Sample self-test report. If you can read this, the held "
        "report carried its attachment through the gate.</p>"
    )
    sample = {
        "from": os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>"),
        "to": [_SELFTEST_CUSTOMER],
        "subject": "Your May 2026 Clarity Report — Self-Test Co",
        "html": "<p>Hi there,</p><p>Your sample Clarity Report is attached.</p><p>— EchoFrame</p>",
        "attachments": [{
            "filename": "EchoFrame_SelfTest.html",
            "content": base64.b64encode(report_html.encode()).decode(),
            "content_type": "text/html",
        }],
    }
    try:
        result = await run_in_threadpool(resend.Emails.send, sample)
    finally:
        review_gate.set_base_url(None)
    held = isinstance(result, dict) and str(result.get("id", "")).startswith("review-held-")
    return JSONResponse({
        "ok": True,
        "held": held,
        "review_email_sent_to": review_gate._owner_email(),
        "customer_on_approve": _SELFTEST_CUSTOMER,
        "note": "Check your inbox for the [REVIEW] email, then click Approve & send.",
    })


@app.get("/api/review/selftest-real")
async def review_selftest_real(request: Request, key: str = ""):
    """Like /selftest, but runs the REAL Auto Ledger engine (real pandas math +
    real Claude-written narrative) on a bundled sample CSV, then routes the
    genuine report through the gate. Locked to the owner's own +alias inbox."""
    if key != _SELFTEST_KEY:
        raise HTTPException(status_code=404, detail="Not found.")
    import shutil
    import auto_ledger_engine as ale

    # selftest_sample.csv ships at the backend root (demo_output/ is gitignored).
    src = BASE_DIR / "selftest_sample.csv"
    if not src.exists():
        src = BASE_DIR / "demo_output" / "auto_ledger_sample_input.csv"
    if not src.exists():
        return JSONResponse({"ok": False, "error": f"sample CSV not found at {src}"}, status_code=500)

    # Stage the sample CSV where the engine looks for this customer's upload.
    try:
        ale.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        dest = ale.UPLOADS_DIR / f"{ale._safe_email(_SELFTEST_CUSTOMER)}.csv"
        shutil.copyfile(src, dest)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"staging failed: {type(e).__name__}: {e}"}, status_code=500)

    # Point the Approve/Hold links back at this same server.
    review_gate.set_base_url(str(request.base_url))
    try:
        path = await run_in_threadpool(
            ale.generate_auto_ledger_report, _SELFTEST_CUSTOMER, "Self-Test Co", "starter", True
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500)
    finally:
        review_gate.set_base_url(None)

    return JSONResponse({
        "ok": True,
        "report_generated": bool(path),
        "product": "Auto Ledger — Starter (real engine + real narrative)",
        "review_email_sent_to": review_gate._owner_email(),
        "customer_on_approve": _SELFTEST_CUSTOMER,
        "note": "Open the [REVIEW] email (real report attached) and click Approve & send.",
    })
