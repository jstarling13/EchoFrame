"""
EchoFrame signed upload tokens
─────────────────────────────────────────────────────────────────────────────
Monthly renewals are silent automatic charges — there is no Stripe Checkout
session to verify against. Instead, when a renewal invoice is paid we mint a
short-lived, signed token that authorises exactly one client to upload exactly
one product's files for exactly one billing period, and email a link carrying
it. The /api/upload endpoint accepts a valid token as an alternative to the
month-1 Stripe-session check.

Token design:
  payload  = email|product|tier|period|exp          (pipe-joined, url-safe)
  sig      = HMAC-SHA256(SIGNING_SECRET, payload)    (hex)
  token    = base64url(payload) + "." + sig

The signature covers email + product + tier + period + expiry, so none of them
can be tampered with. Verification is constant-time and rejects expired tokens.
The secret comes from the SIGNING_SECRET env var and is never embedded in code.
"""

from __future__ import annotations

import os
import hmac
import time
import base64
import hashlib
from typing import Optional
from urllib.parse import urlencode, quote


_SEP = "|"


def _secret() -> bytes:
    secret = os.environ.get("SIGNING_SECRET", "")
    if not secret:
        # Fail loudly at use-time (not import-time) so the app still boots for
        # the month-1 flow even before SIGNING_SECRET is configured.
        raise RuntimeError(
            "SIGNING_SECRET is not set — required to sign/verify renewal upload links."
        )
    return secret.encode("utf-8")


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_token(
    email: str,
    product: str,
    tier: str,
    period: str,
    ttl_seconds: int = 14 * 24 * 3600,
    *,
    _now: Optional[int] = None,
) -> str:
    """Mint a signed upload token. Default lifetime: 14 days (covers the billing
    cycle plus a comfortable grace window)."""
    now = int(_now if _now is not None else time.time())
    exp = now + int(ttl_seconds)
    # Guard against pipes in fields breaking the payload split.
    parts = [
        (email or "").strip().lower().replace(_SEP, ""),
        (product or "").strip().replace(_SEP, ""),
        (tier or "").strip().replace(_SEP, ""),
        (period or "").strip().replace(_SEP, ""),
        str(exp),
    ]
    payload = _SEP.join(parts)
    sig = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{_b64url(payload.encode('utf-8'))}.{sig}"


def verify_token(token: str, *, _now: Optional[int] = None) -> Optional[dict]:
    """Validate a token's signature and expiry.

    Returns {email, product, tier, period, exp} on success, or None on any
    failure (malformed, bad signature, expired). Constant-time comparison.
    """
    if not token or "." not in token:
        return None
    b64_payload, _, sig = token.partition(".")
    try:
        payload = _b64url_decode(b64_payload).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None

    try:
        expected = hmac.new(
            _secret(), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    except RuntimeError:
        return None

    # Constant-time comparison — never a plain `==` on the signature.
    if not hmac.compare_digest(expected, sig):
        return None

    parts = payload.split(_SEP)
    if len(parts) != 5:
        return None
    email, product, tier, period, exp_str = parts
    try:
        exp = int(exp_str)
    except ValueError:
        return None

    now = int(_now if _now is not None else time.time())
    if exp <= now:
        return None

    return {
        "email": email,
        "product": product,
        "tier": tier,
        "period": period,
        "exp": exp,
    }


# ── Client-portal auth tokens ───────────────────────────────────────────────
# The portal reuses the exact HMAC machinery above — no passwords, no database.
# Two token kinds, each with a distinct `purpose` tag baked into the signed
# payload so one can never be replayed as the other:
#
#   login    — emailed magic-link token; short-lived (default 20 min), single-use
#              (single-use is enforced separately in the store via a nonce).
#   session  — the value stored in the httpOnly session cookie after a successful
#              magic-link click; long-lived (default 30 days).
#
# Payload shape:  purpose|email|exp   (3 parts — distinct from the 5-part upload
# token, so verify_token and these verifiers can never be confused.)

_LOGIN_TTL_DEFAULT   = 20 * 60            # 20 minutes
_SESSION_TTL_DEFAULT = 30 * 24 * 3600     # 30 days


def _make_auth_token(purpose: str, email: str, ttl_seconds: int, _now: Optional[int]) -> str:
    now = int(_now if _now is not None else time.time())
    exp = now + int(ttl_seconds)
    payload = _SEP.join([
        purpose,
        (email or "").strip().lower().replace(_SEP, ""),
        str(exp),
    ])
    sig = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{_b64url(payload.encode('utf-8'))}.{sig}"


def _verify_auth_token(purpose: str, token: str, _now: Optional[int]) -> Optional[str]:
    """Return the email if the token is valid, unexpired, and of the expected
    purpose; otherwise None. Constant-time signature comparison."""
    if not token or "." not in token:
        return None
    b64_payload, _, sig = token.partition(".")
    try:
        payload = _b64url_decode(b64_payload).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    try:
        expected = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    except RuntimeError:
        return None
    if not hmac.compare_digest(expected, sig):
        return None
    parts = payload.split(_SEP)
    if len(parts) != 3:
        return None
    tok_purpose, email, exp_str = parts
    if tok_purpose != purpose:
        return None
    try:
        exp = int(exp_str)
    except ValueError:
        return None
    now = int(_now if _now is not None else time.time())
    if exp <= now:
        return None
    return email


def make_login_token(email: str, ttl_seconds: int = _LOGIN_TTL_DEFAULT, *, _now: Optional[int] = None) -> str:
    """Mint a short-lived magic-link login token for `email`."""
    return _make_auth_token("login", email, ttl_seconds, _now)


def verify_login_token(token: str, *, _now: Optional[int] = None) -> Optional[str]:
    """Validate a magic-link token; return the email on success, else None."""
    return _verify_auth_token("login", token, _now)


def make_session_token(email: str, ttl_seconds: int = _SESSION_TTL_DEFAULT, *, _now: Optional[int] = None) -> str:
    """Mint the signed value stored in the portal session cookie."""
    return _make_auth_token("session", email, ttl_seconds, _now)


def verify_session_token(token: str, *, _now: Optional[int] = None) -> Optional[str]:
    """Validate a session-cookie value; return the email on success, else None."""
    return _verify_auth_token("session", token, _now)


def token_fingerprint(token: str) -> str:
    """A short, non-reversible fingerprint of a token — used as a store key for
    single-use enforcement so the raw token never lands in the datastore."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]


def build_upload_url(base_url: str, email: str, product: str, tier: str, token: str) -> str:
    """Build the client-facing upload link for a renewal.

    Revenue Suite needs three files, so it has its own page; every other product
    uses the shared per-product intake page at /upload.
    """
    base = (base_url or "").rstrip("/")
    if product == "revenue-suite":
        path = "/upload/revenue-suite"
        query = urlencode({"email": email, "token": token})
    else:
        path = "/upload"
        query = urlencode(
            {"email": email, "product": product, "tier": tier, "token": token}
        )
    return f"{base}{path}?{query}"
