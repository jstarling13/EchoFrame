"""
EchoFrame client portal — passwordless magic-link login
─────────────────────────────────────────────────────────────────────────────
A self-service area where a paying client signs in to manage their account. It
deliberately reuses the EXACT primitives the rest of the app already runs on, so
it adds **no passwords, no new database, and no new security surface**:

  • sign.py    — HMAC magic-link + session tokens (same machinery as upload links)
  • store.py   — durable customer + period records (Upstash; in-memory in dev)
  • emails.py  — Resend for the sign-in email
  • Stripe     — billing_portal.Session for self-serve subscription management

Flow
  1. Client enters their email on the static site (site/login.html), which
     POSTs to /portal/login here.
  2. We mint a single-use, 20-minute magic-link token, store a nonce, and email
     the link. (Anti-enumeration: the confirmation page looks identical whether
     or not the email belongs to a customer; we only actually send to customers.)
  3. Clicking the link hits /portal/auth, which verifies + consumes the token,
     sets an httpOnly signed session cookie, and lands them in the portal.
  4. /portal pages read that cookie. No server-side session store needed — the
     cookie value is a signed (email|exp) token we can verify statelessly.

The whole module is mounted by main.register_portal(app, limiter) so it shares
the app's rate limiter and exception handlers without a circular import.
"""

from __future__ import annotations

import os
import re
import html
import traceback

import stripe
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import store
import sign
import emails
from registry import get_product

# ── Config ──────────────────────────────────────────────────────────────────

SESSION_COOKIE   = "ef_session"
SESSION_MAX_AGE  = 30 * 24 * 3600          # keep in step with sign.make_session_token
LOGIN_TTL        = 20 * 60                  # magic-link lifetime (also the nonce TTL)

# Email validation mirrors main.py exactly so the same address normalises to the
# same store key in both modules.
_EMAIL_RE     = re.compile(r'^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,}$')
_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')


def _base_url() -> str:
    return (os.environ.get("PUBLIC_BASE_URL", "") or "").rstrip("/")


def _cookie_secure() -> bool:
    # Secure cookies are only sent over https. PUBLIC_BASE_URL is https in
    # production (Railway); http://localhost in dev, where we must NOT set Secure
    # or the browser would silently drop the cookie.
    return _base_url().startswith("https://")


def _valid_email(email: str) -> str | None:
    email = (email or "").strip().lower()
    if not email or len(email) > 320 or not _EMAIL_RE.match(email):
        return None
    return email


def _safe_email(email: str) -> str:
    email = (email or "").strip().lower()
    local, _, domain = email.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', local)}_at_{_SAFE_CHAR_RE.sub('_', domain)}"


def _session_email(request: Request) -> str | None:
    """Return the signed-in client's email, or None if no valid session."""
    raw = request.cookies.get(SESSION_COOKIE, "")
    if not raw:
        return None
    return sign.verify_session_token(raw)


# ── Inline HTML (self-contained; mirrors the look of the intake pages) ────────

_STYLE = """
  :root{--navy:#012A4A;--blue:#1E90FF;--blue-soft:#DBEAFE;--ink:#111827;
        --ink-soft:#4B5563;--ink-faint:#6B7280;--line:#E5E7EB;--bg:#FFFFFF;--bg-soft:#F9FAFB;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
       font-size:16px;line-height:1.6;background:var(--bg-soft);color:var(--ink);
       -webkit-font-smoothing:antialiased;padding:40px 16px;}
  .wrap{max-width:680px;margin:0 auto;}
  .card{background:var(--bg);border:1px solid var(--line);border-radius:14px;
        padding:28px;margin-bottom:20px;}
  h1{font-size:24px;color:var(--navy);margin-bottom:6px;}
  h2{font-size:17px;color:var(--navy);margin-bottom:14px;}
  p{color:var(--ink-soft);margin-bottom:10px;}
  .muted{color:var(--ink-faint);font-size:14px;}
  label{display:block;font-size:13px;font-weight:600;color:var(--ink);margin:12px 0 4px;}
  input[type=text],input[type=email]{width:100%;padding:11px 12px;border:1px solid var(--line);
        border-radius:8px;font-size:15px;}
  .btn{display:inline-block;background:var(--blue);color:#fff;font-weight:600;border:none;
       padding:12px 20px;border-radius:8px;text-decoration:none;cursor:pointer;font-size:15px;}
  .btn.secondary{background:var(--bg);color:var(--navy);border:1px solid var(--line);}
  .row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;}
  table{width:100%;border-collapse:collapse;margin-top:8px;}
  th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);font-size:14px;}
  th{color:var(--ink-faint);font-weight:600;}
  .pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;}
  .pill.ok{background:#DCFCE7;color:#166534;}
  .pill.wait{background:var(--blue-soft);color:#1E3A8A;}
  .topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;}
  a.link{color:var(--blue);text-decoration:none;font-weight:600;}
"""


def _page(title: str, body: str) -> str:
    return (
        f"<!doctype html><html lang=en><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body><div class=wrap>{body}</div></body></html>"
    )


def _esc(v: object) -> str:
    return html.escape(str(v if v is not None else ""))


# ── Route handlers ────────────────────────────────────────────────────────────

async def _login(request: Request, email: str = Form("")) -> HTMLResponse:
    """Receive the email from the static login page, email a magic link if the
    address belongs to a customer, and always show the same confirmation."""
    valid = _valid_email(email)
    if not valid:
        body = (
            "<div class=card><h1>Sign in to EchoFrame</h1>"
            "<p>That doesn't look like a valid email address. Please go back and try again.</p>"
            f"<p><a class=link href='{_base_url()}/'>← Back to echoframe.net</a></p></div>"
        )
        return HTMLResponse(_page("Sign in — EchoFrame", body), status_code=400)

    # Only mint + send to a known customer, but never reveal which it was.
    try:
        rec = store.load_customer_record(_safe_email(valid))
        if rec:
            token = sign.make_login_token(valid, ttl_seconds=LOGIN_TTL)
            store.register_login_nonce(sign.token_fingerprint(token), valid, LOGIN_TTL)
            login_url = f"{_base_url()}/portal/auth?token={token}"
            emails.send_login_link(valid, (rec.get("name") or "").strip(), login_url)
            print("[EchoFrame] Portal sign-in link sent.")  # no PII
        else:
            print("[EchoFrame] Portal sign-in requested for unknown email (no send).")
    except Exception:
        # Never surface internal errors to the visitor; never leak existence.
        print(f"[EchoFrame] PORTAL login error:\n{traceback.format_exc()}", flush=True)

    body = (
        "<div class=card><h1>Check your email</h1>"
        "<p>If that address has an EchoFrame account, we just sent a secure sign-in "
        "link to it. It works once and expires in 20 minutes.</p>"
        "<p class=muted>Didn't get it? Check spam, or head back and try again.</p>"
        f"<p><a class=link href='{_base_url()}/'>← Back to echoframe.net</a></p></div>"
    )
    return HTMLResponse(_page("Check your email — EchoFrame", body))


async def _auth(request: Request, token: str = "") -> RedirectResponse | HTMLResponse:
    """Consume a magic-link token: verify signature/expiry, burn the single-use
    nonce, set the session cookie, and redirect into the portal."""
    email = sign.verify_login_token(token)
    if not email or not store.consume_login_nonce(sign.token_fingerprint(token), email):
        body = (
            "<div class=card><h1>Link expired</h1>"
            "<p>This sign-in link is invalid, has expired, or was already used. "
            "Sign-in links work once and last 20 minutes.</p>"
            f"<p><a class=link href='{_base_url()}/login.html'>Request a new link →</a></p></div>"
        )
        return HTMLResponse(_page("Link expired — EchoFrame", body), status_code=400)

    resp = RedirectResponse(url="/portal", status_code=303)
    resp.set_cookie(
        key=SESSION_COOKIE,
        value=sign.make_session_token(email, ttl_seconds=SESSION_MAX_AGE),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    return resp


async def _logout(request: Request) -> RedirectResponse:
    resp = RedirectResponse(url=f"{_base_url()}/login.html" if _base_url() else "/portal/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


def _product_label(slug: str) -> str:
    try:
        return get_product(slug).label
    except Exception:
        return slug or "Report"


async def _dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    email = _session_email(request)
    if not email:
        # Not signed in → bounce to the static login page.
        target = f"{_base_url()}/login.html" if _base_url() else "/portal/login"
        return RedirectResponse(url=target, status_code=303)

    safe = _safe_email(email)
    rec = store.load_customer_record(safe) or {"email": email}
    periods = store.list_customer_periods(safe)
    pending = [p for p in periods if not p.get("uploaded")]

    biz   = _esc(rec.get("business_name", ""))
    name  = _esc(rec.get("name", ""))
    indus = _esc(rec.get("industry", ""))
    loc   = _esc(rec.get("location", ""))
    has_stripe = bool((rec.get("stripe_customer") or "").strip())

    # ── Top bar ──
    top = (
        "<div class=topbar>"
        f"<div><h1>Your EchoFrame account</h1><p class=muted>{_esc(email)}</p></div>"
        "<a class='btn secondary' href='/portal/logout'>Sign out</a>"
        "</div>"
    )

    # ── Subscription / billing ──
    if has_stripe:
        billing = (
            "<div class=card><h2>Subscription &amp; billing</h2>"
            "<p>Update your card, view invoices, or cancel — managed securely through Stripe.</p>"
            "<a class=btn href='/portal/billing'>Manage billing →</a></div>"
        )
    else:
        billing = (
            "<div class=card><h2>Subscription &amp; billing</h2>"
            "<p class=muted>We don't have a billing profile linked to this email yet. "
            "Once your first subscription is active, you'll manage it here.</p></div>"
        )

    # ── This month's upload ──
    if pending:
        p = pending[0]
        upload = (
            "<div class=card><h2>This month's report</h2>"
            f"<p>We're ready for your numbers for <strong>{_esc(p.get('period_label') or p.get('period'))}</strong> "
            f"({_esc(_product_label(p.get('product','')))}).</p>"
            "<a class=btn href='/portal/upload'>Upload this month's file →</a></div>"
        )
    else:
        upload = (
            "<div class=card><h2>This month's report</h2>"
            "<p class=muted>Nothing to upload right now. When your next cycle is billed, "
            "your upload link will appear here and arrive by email.</p></div>"
        )

    # ── Report history ──
    if periods:
        rows = ""
        for p in periods:
            status = ("<span class='pill ok'>Received</span>" if p.get("uploaded")
                      else "<span class='pill wait'>Awaiting upload</span>")
            rows += (
                f"<tr><td>{_esc(p.get('period_label') or p.get('period'))}</td>"
                f"<td>{_esc(_product_label(p.get('product','')))}</td>"
                f"<td>{status}</td></tr>"
            )
        history = (
            "<div class=card><h2>Report history</h2>"
            "<table><tr><th>Period</th><th>Report</th><th>Status</th></tr>"
            f"{rows}</table>"
            "<p class=muted style='margin-top:12px'>Reports are emailed to you when ready. "
            "Downloadable copies in the portal are coming soon.</p></div>"
        )
    else:
        history = (
            "<div class=card><h2>Report history</h2>"
            "<p class=muted>Your billing periods will appear here after your next monthly cycle.</p></div>"
        )

    # ── Business profile ──
    profile = (
        "<div class=card><h2>Business profile</h2>"
        "<p class=muted>Keep this current so your reports stay personalized.</p>"
        "<form method=post action='/portal/profile'>"
        f"<label>Business name</label><input type=text name=business_name value='{biz}' maxlength=200>"
        f"<label>Contact name</label><input type=text name=name value='{name}' maxlength=200>"
        f"<label>Industry</label><input type=text name=industry value='{indus}' maxlength=200>"
        f"<label>Location</label><input type=text name=location value='{loc}' maxlength=200>"
        "<div class=row style='margin-top:16px'><button class=btn type=submit>Save profile</button></div>"
        "</form></div>"
    )

    body = top + billing + upload + history + profile
    return HTMLResponse(_page("Your EchoFrame account", body))


async def _save_profile(
    request: Request,
    business_name: str = Form(""),
    name: str = Form(""),
    industry: str = Form(""),
    location: str = Form(""),
) -> RedirectResponse:
    email = _session_email(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not signed in.")
    store.save_customer_record(_safe_email(email), {
        "email": email,
        "business_name": business_name.strip()[:200],
        "name": name.strip()[:200],
        "industry": industry.strip()[:200],
        "location": location.strip()[:200],
    })
    return RedirectResponse(url="/portal", status_code=303)


async def _billing(request: Request) -> RedirectResponse | HTMLResponse:
    """Redirect the signed-in client into Stripe's hosted Customer Portal."""
    email = _session_email(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not signed in.")
    rec = store.load_customer_record(_safe_email(email)) or {}
    customer_id = (rec.get("stripe_customer") or "").strip()
    if not customer_id:
        body = ("<div class=card><h1>No billing profile</h1>"
                "<p>We couldn't find a Stripe customer linked to your account yet.</p>"
                "<p><a class=link href='/portal'>← Back to your account</a></p></div>")
        return HTMLResponse(_page("Billing — EchoFrame", body), status_code=404)
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{_base_url()}/portal" if _base_url() else None,
        )
    except Exception:
        print(f"[EchoFrame] PORTAL billing error:\n{traceback.format_exc()}", flush=True)
        body = ("<div class=card><h1>Billing is temporarily unavailable</h1>"
                "<p>Please try again in a moment, or reply to your last EchoFrame email and "
                "we'll sort it out.</p>"
                "<p><a class=link href='/portal'>← Back to your account</a></p></div>")
        return HTMLResponse(_page("Billing — EchoFrame", body), status_code=502)
    return RedirectResponse(url=session.url, status_code=303)


async def _start_upload(request: Request) -> RedirectResponse | HTMLResponse:
    """Mint a fresh upload token for the client's most recent pending period and
    hand them off to the existing /upload intake page."""
    email = _session_email(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not signed in.")
    safe = _safe_email(email)
    pending = [p for p in store.list_customer_periods(safe) if not p.get("uploaded")]
    if not pending:
        return RedirectResponse(url="/portal", status_code=303)
    p = pending[0]
    slug = p.get("product", "")
    tier = p.get("tier", "")
    period = p.get("period", "")
    token = sign.make_token(email, slug, tier, period)
    url = sign.build_upload_url(_base_url(), email, slug, tier, token)
    return RedirectResponse(url=url, status_code=303)


def register_portal(app, limiter) -> None:
    """Mount the portal routes on the FastAPI app, reusing its rate limiter.

    Called from main.py after `app` and `limiter` are created, which avoids a
    circular import while letting the login endpoint share slowapi limiting."""
    # response_model=None: these handlers return raw Starlette Responses (and
    # unions thereof), which FastAPI must not try to coerce into a Pydantic model.
    app.add_api_route("/portal", _dashboard, methods=["GET"], response_class=HTMLResponse, response_model=None)
    app.add_api_route("/portal/auth", _auth, methods=["GET"], response_model=None)
    app.add_api_route("/portal/logout", _logout, methods=["GET"], response_model=None)
    app.add_api_route("/portal/billing", _billing, methods=["GET"], response_model=None)
    app.add_api_route("/portal/upload", _start_upload, methods=["GET"], response_model=None)
    app.add_api_route("/portal/profile", _save_profile, methods=["POST"], response_model=None)
    # Rate-limit the email-sending endpoint to blunt abuse / enumeration probing.
    app.add_api_route(
        "/portal/login",
        limiter.limit("5/minute")(_login),
        methods=["POST"],
        response_class=HTMLResponse,
        response_model=None,
    )
