"""
Tests for the magic-link client portal (portal.py + the sign/store additions).

Fully offline: the resend SDK is stubbed before import, and the durable store
falls back to its in-memory backend. PUBLIC_BASE_URL is http:// so the session
cookie is not marked Secure and the TestClient will actually send it back.
"""
import os
import sys
import types
import time

import pytest

# Must be set before importing sign/main (sign._secret raises without it).
# Use setdefault so we never clobber values another test module already set —
# e.g. test_renewals pins PUBLIC_BASE_URL and asserts on it. (main reads
# PUBLIC_BASE_URL once at import; portal reads os.environ live, so the portal
# routes are base-URL-agnostic in these tests.) The session cookie's Secure flag
# is forced off via monkeypatch below so the http TestClient retains the cookie.
os.environ.setdefault("SIGNING_SECRET", "portal-test-signing-secret")
# Match the value test_renewals pins. main caches PUBLIC_BASE_URL at first import,
# and this module may be imported first — using the same value keeps both modules'
# expectations consistent regardless of collection order.
os.environ.setdefault("PUBLIC_BASE_URL", "https://app.echoframe.net")

# Stub the resend SDK so sending a sign-in link never touches the network.
_sent = []
_fake_resend = types.ModuleType("resend")
class _Emails:
    @staticmethod
    def send(params, *a, **k):
        _sent.append(params)
        return {"id": f"test-{len(_sent)}"}
_fake_resend.Emails = _Emails
_fake_resend.api_key = ""
sys.modules["resend"] = _fake_resend

from fastapi.testclient import TestClient  # noqa: E402

import sign       # noqa: E402
import store      # noqa: E402
import portal     # noqa: E402
from main import app  # noqa: E402

client = TestClient(app, follow_redirects=False)

CUST = "owner@acme-test.com"


def _reset_store():
    """Wipe the in-memory store so portal-test seed data never leaks into other
    modules' tests (the in-memory backend is a process-global shared by all)."""
    if not store.is_configured():
        store._mem.clear()
        store._mem_sets.clear()


@pytest.fixture(autouse=True)
def _seed_and_clear(monkeypatch):
    # Force the session cookie non-Secure regardless of PUBLIC_BASE_URL, so the
    # http:// TestClient stores and replays it (a Secure cookie is dropped over http).
    monkeypatch.setattr(portal, "_cookie_secure", lambda: False)
    _reset_store()
    _sent.clear()
    # A known customer with a Stripe id and one pending period.
    safe = portal._safe_email(CUST)
    store.save_customer_record(safe, {
        "email": CUST, "name": "Pat Owner", "stripe_customer": "cus_test_123",
    })
    store.mark_period_billed(safe, "2026-05", {
        "email": CUST, "name": "Pat Owner", "product": "auto-ledger", "tier": "pro",
        "period": "2026-05", "period_label": "May 2026", "uploaded": False,
    })
    yield
    _reset_store()


# ── token layer ───────────────────────────────────────────────────────────────

def test_login_token_roundtrip_and_purpose_isolation():
    tok = sign.make_login_token(CUST)
    assert sign.verify_login_token(tok) == CUST
    # A login token must NOT validate as a session token, and vice-versa.
    assert sign.verify_session_token(tok) is None
    sess = sign.make_session_token(CUST)
    assert sign.verify_session_token(sess) == CUST
    assert sign.verify_login_token(sess) is None
    # ...and neither validates as a 5-part upload token.
    assert sign.verify_token(tok) is None


def test_login_token_expiry_and_tamper():
    now = 1_000_000
    tok = sign.make_login_token(CUST, ttl_seconds=10, _now=now)
    assert sign.verify_login_token(tok, _now=now + 5) == CUST
    assert sign.verify_login_token(tok, _now=now + 11) is None      # expired
    assert sign.verify_login_token(tok[:-1] + ("0" if tok[-1] != "0" else "1")) is None  # bad sig


def test_single_use_nonce():
    tok = sign.make_login_token(CUST)
    fp = sign.token_fingerprint(tok)
    store.register_login_nonce(fp, CUST, 600)
    assert store.consume_login_nonce(fp, CUST) is True     # first use
    assert store.consume_login_nonce(fp, CUST) is False    # already consumed
    # Mismatched email never consumes.
    tok2 = sign.make_login_token(CUST)
    fp2 = sign.token_fingerprint(tok2)
    store.register_login_nonce(fp2, CUST, 600)
    assert store.consume_login_nonce(fp2, "someone@else.com") is False


def test_customer_period_index():
    rows = store.list_customer_periods(portal._safe_email(CUST))
    assert [r["period"] for r in rows] == ["2026-05"]


# ── HTTP flow ─────────────────────────────────────────────────────────────────

def test_login_unknown_email_sends_nothing_but_confirms():
    r = client.post("/portal/login", data={"email": "nobody@nowhere.test"})
    assert r.status_code == 200
    assert "Check your email" in r.text
    assert _sent == []   # anti-enumeration: no email to a non-customer


def test_login_known_email_sends_link():
    r = client.post("/portal/login", data={"email": CUST})
    assert r.status_code == 200
    assert "Check your email" in r.text
    assert len(_sent) == 1
    assert _sent[0]["to"] == [CUST]
    assert "/portal/auth?token=" in _sent[0]["html"]


def test_login_invalid_email_rejected():
    r = client.post("/portal/login", data={"email": "not-an-email"})
    assert r.status_code == 400
    assert _sent == []


def _mint_and_send_link() -> str:
    """Drive a real login to obtain a usable magic-link token."""
    client.post("/portal/login", data={"email": CUST})
    html = _sent[-1]["html"]
    token = html.split("/portal/auth?token=")[1].split('"')[0]
    return token


def test_auth_sets_session_and_is_single_use():
    token = _mint_and_send_link()
    # First click: authenticated, redirected into the portal, cookie set.
    r = client.get(f"/portal/auth?token={token}")
    assert r.status_code == 303
    assert r.headers["location"] == "/portal"
    assert portal.SESSION_COOKIE in r.cookies or portal.SESSION_COOKIE in client.cookies

    # Second click with the same link is rejected (nonce already burned).
    fresh = TestClient(app, follow_redirects=False)
    r2 = fresh.get(f"/portal/auth?token={token}")
    assert r2.status_code == 400
    assert "expired" in r2.text.lower()


def test_dashboard_requires_session():
    anon = TestClient(app, follow_redirects=False)
    r = anon.get("/portal")
    assert r.status_code == 303
    assert "login.html" in r.headers["location"]


def test_authenticated_dashboard_shows_account():
    token = _mint_and_send_link()
    client.get(f"/portal/auth?token={token}")          # establishes the cookie
    r = client.get("/portal")
    assert r.status_code == 200
    assert CUST in r.text
    assert "May 2026" in r.text                          # period history
    assert "Manage billing" in r.text                    # has stripe_customer


def test_profile_save_persists():
    token = _mint_and_send_link()
    client.get(f"/portal/auth?token={token}")
    r = client.post("/portal/profile", data={
        "business_name": "Acme Diner", "name": "Pat Owner",
        "industry": "Restaurant", "location": "Columbus, GA",
    })
    assert r.status_code == 303
    rec = store.load_customer_record(portal._safe_email(CUST))
    assert rec["business_name"] == "Acme Diner"
    assert rec["industry"] == "Restaurant"


def test_start_upload_redirects_to_signed_upload_link():
    token = _mint_and_send_link()
    client.get(f"/portal/auth?token={token}")
    r = client.get("/portal/upload")
    assert r.status_code == 303
    loc = r.headers["location"]
    assert "/upload" in loc and "token=" in loc


def test_logout_clears_cookie():
    token = _mint_and_send_link()
    client.get(f"/portal/auth?token={token}")
    r = client.get("/portal/logout")
    assert r.status_code == 303
    # After logout the protected page bounces to login again.
    after = client.get("/portal")
    assert after.status_code == 303
    assert "login.html" in after.headers["location"]
