"""
EchoFrame recurring-renewal tests
─────────────────────────────────────────────────────────────────────────────
Covers the monthly fulfilment loop added on top of the month-1 signup flow:

  • signed upload tokens — round-trip, tamper, expiry, email binding
  • invoice.payment_succeeded webhook — acts on renewals (subscription_cycle),
    skips the first invoice (subscription_create), idempotent
  • /api/upload accepting a valid token as an alternative to a Stripe session,
    and rejecting bad / expired tokens
  • the reminder cron endpoint's CRON_SECRET gate

Run with:  pytest tests/test_renewals.py -v
"""

import os
import json
import time
import hmac
import hashlib
import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

# Required + renewal env must be set BEFORE importing main.
_ENV = {
    "STRIPE_SECRET_KEY":     "sk_test_placeholder",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_placeholder",
    "ANTHROPIC_API_KEY":     "sk-ant-test-placeholder",
    "RESEND_API_KEY":        "re_test_placeholder",
    "SIGNING_SECRET":        "unit-test-signing-secret",
    "PUBLIC_BASE_URL":       "https://app.echoframe.net",
}
for _k, _v in _ENV.items():
    if not os.environ.get(_k):
        os.environ[_k] = _v

import main          # noqa: E402
import sign          # noqa: E402
import store         # noqa: E402


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _no_rate_limits():
    main.limiter.enabled = False
    yield
    main.limiter.enabled = False


def _signed_webhook(event: dict) -> tuple[bytes, str]:
    """Build a payload + a stripe-signature for the test secret (construct_event
    is mocked in these tests, so the signature only needs the header to exist)."""
    payload = json.dumps(event).encode("utf-8")
    ts = str(int(time.time()))
    mac = hmac.new(b"x", f"{ts}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()
    return payload, f"t={ts},v1={mac}"


def _invoice(billing_reason: str, product_id: str, email="client@example.com",
             name="Dana Owner", period_start=None) -> dict:
    return {
        "id": "in_test_" + billing_reason,
        "billing_reason": billing_reason,
        "customer": "cus_test_123",
        "customer_email": email,
        "customer_name": name,
        "period_start": period_start or int(time.time()),
        "lines": {"data": [{
            "period": {"start": period_start or int(time.time())},
            "price": {"product": product_id},
        }]},
    }


# ── Signed tokens ─────────────────────────────────────────────────────────────

class TestSignedTokens:
    def test_round_trip(self):
        t = sign.make_token("a@b.com", "auto-ledger", "growth", "2026-06")
        p = sign.verify_token(t)
        assert p == {"email": "a@b.com", "product": "auto-ledger", "tier": "growth",
                     "period": "2026-06", "exp": p["exp"]}

    def test_tampered_signature_rejected(self):
        t = sign.make_token("a@b.com", "clarity", "", "2026-06")
        flipped = t[:-1] + ("0" if t[-1] != "0" else "1")
        assert sign.verify_token(flipped) is None

    def test_tampered_payload_rejected(self):
        t = sign.make_token("a@b.com", "clarity", "", "2026-06")
        body, _, sig = t.partition(".")
        forged = sign._b64url(b"attacker@evil.com|clarity||2026-06|9999999999") + "." + sig
        assert sign.verify_token(forged) is None

    def test_expired_rejected(self):
        t = sign.make_token("a@b.com", "clarity", "", "2026-06", ttl_seconds=-5)
        assert sign.verify_token(t) is None

    def test_garbage_rejected(self):
        assert sign.verify_token("") is None
        assert sign.verify_token("not-a-token") is None
        assert sign.verify_token("a.b.c") is None


# ── invoice.payment_succeeded webhook ─────────────────────────────────────────

@pytest.mark.asyncio
class TestInvoiceWebhook:

    async def test_renewal_sends_upload_link_and_records_period(self, client):
        store._mem.clear(); store._mem_sets.clear()
        # prod_UZ9RW25uUul5eB → clarity (from registry.STRIPE_PRODUCT_MAP)
        event = {"id": "evt_renewal_1", "type": "invoice.payment_succeeded",
                 "data": {"object": _invoice("subscription_cycle", "prod_UZ9RW25uUul5eB")}}
        _, sig = _signed_webhook(event)

        with patch("main.stripe.Webhook.construct_event", return_value=event), \
             patch("main.emails.send_upload_link") as mock_send:
            r = await client.post("/webhook/stripe", content=json.dumps(event).encode(),
                                  headers={"stripe-signature": sig})

        assert r.status_code == 200
        mock_send.assert_called_once()
        # link is built from PUBLIC_BASE_URL and carries a token
        _args, kwargs = mock_send.call_args
        sent_url = mock_send.call_args[0][3]
        assert sent_url.startswith("https://app.echoframe.net/upload")
        assert "token=" in sent_url
        # period recorded as billed + pending
        pending = store.list_pending_periods()
        assert len(pending) == 1
        safe, period = pending[0]
        rec = store.load_period(safe, period)
        assert rec["product"] == "clarity" and rec["uploaded"] is False

    async def test_first_invoice_does_not_double_send(self, client):
        store._mem.clear(); store._mem_sets.clear()
        event = {"id": "evt_first_1", "type": "invoice.payment_succeeded",
                 "data": {"object": _invoice("subscription_create", "prod_UZ9RW25uUul5eB")}}
        _, sig = _signed_webhook(event)

        with patch("main.stripe.Webhook.construct_event", return_value=event), \
             patch("main.emails.send_upload_link") as mock_send:
            r = await client.post("/webhook/stripe", content=json.dumps(event).encode(),
                                  headers={"stripe-signature": sig})

        assert r.status_code == 200
        mock_send.assert_not_called()
        assert store.list_pending_periods() == []

    async def test_unroutable_product_does_not_send(self, client):
        store._mem.clear(); store._mem_sets.clear()
        event = {"id": "evt_unknown_prod", "type": "invoice.payment_succeeded",
                 "data": {"object": _invoice("subscription_cycle", "prod_DOES_NOT_EXIST")}}
        _, sig = _signed_webhook(event)

        with patch("main.stripe.Webhook.construct_event", return_value=event), \
             patch("main.emails.send_upload_link") as mock_send:
            r = await client.post("/webhook/stripe", content=json.dumps(event).encode(),
                                  headers={"stripe-signature": sig})

        assert r.status_code == 200
        mock_send.assert_not_called()  # never guess a product → no link sent

    async def test_renewal_is_idempotent(self, client):
        store._mem.clear(); store._mem_sets.clear()
        event = {"id": "evt_renewal_dup", "type": "invoice.payment_succeeded",
                 "data": {"object": _invoice("subscription_cycle", "prod_UZ9RW25uUul5eB")}}
        _, sig = _signed_webhook(event)

        with patch("main.stripe.Webhook.construct_event", return_value=event), \
             patch("main.emails.send_upload_link") as mock_send:
            r1 = await client.post("/webhook/stripe", content=json.dumps(event).encode(),
                                   headers={"stripe-signature": sig})
            r2 = await client.post("/webhook/stripe", content=json.dumps(event).encode(),
                                   headers={"stripe-signature": sig})

        assert r1.status_code == 200 and r2.status_code == 200
        assert r2.json().get("note") == "duplicate"
        assert mock_send.call_count == 1  # second delivery did not re-send


# ── /api/upload with a signed token ───────────────────────────────────────────

@pytest.mark.asyncio
class TestTokenUpload:

    async def test_valid_token_accepts_upload_without_stripe(self, client):
        store._mem.clear(); store._mem_sets.clear()
        email = "renewal@example.com"
        token = sign.make_token(email, "clarity", "", "2026-06")
        # pre-record the billed period so we can assert it gets cleared
        store.mark_period_billed(main._safe_email(email), "2026-06", {
            "email": email, "name": "Dana", "product": "clarity", "tier": "",
            "period": "2026-06", "billed_at": int(time.time()),
            "uploaded": False, "reminded": False,
        })

        with patch("main._run_report_sync") as mock_run:
            r = await client.post("/api/upload", data={
                "email": email, "session_id": "", "token": token,
                "industry": "Restaurant", "location": "Columbus GA",
            }, files={"file": ("pnl.csv", b"_Business Name,Dana Co\nRevenue,1000,900\n", "text/csv")})

        assert r.status_code == 200, r.text
        assert r.json()["product"] == "clarity"
        mock_run.assert_called_once()
        # period marked uploaded → no longer pending
        assert store.list_pending_periods() == []

    async def test_token_email_mismatch_rejected(self, client):
        token = sign.make_token("owner@example.com", "clarity", "", "2026-06")
        r = await client.post("/api/upload", data={
            "email": "attacker@evil.com", "session_id": "", "token": token,
            "industry": "Restaurant", "location": "Columbus GA",
        }, files={"file": ("pnl.csv", b"Revenue,1000\n", "text/csv")})
        assert r.status_code == 403

    async def test_expired_token_rejected(self, client):
        token = sign.make_token("owner@example.com", "clarity", "", "2026-06", ttl_seconds=-5)
        r = await client.post("/api/upload", data={
            "email": "owner@example.com", "session_id": "", "token": token,
            "industry": "Restaurant", "location": "Columbus GA",
        }, files={"file": ("pnl.csv", b"Revenue,1000\n", "text/csv")})
        assert r.status_code == 403

    async def test_token_overrides_product_field(self, client):
        """A client cannot swap to a different (cheaper/other) product via the form —
        the signed token's product wins."""
        store._mem.clear(); store._mem_sets.clear()
        email = "swap@example.com"
        token = sign.make_token(email, "drive-pay", "", "2026-06")
        with patch("main._run_report_sync") as mock_run:
            r = await client.post("/api/upload", data={
                "email": email, "session_id": "", "token": token,
                "product": "auto-ledger",  # attempt to override — must be ignored
            }, files={"file": ("ros.csv", b"col\n1\n", "text/csv")})
        assert r.status_code == 200, r.text
        assert r.json()["product"] == "drive-pay"


# ── Reminder cron endpoint ────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCronEndpoint:

    async def test_cron_requires_secret_when_set(self, client):
        with patch.dict(os.environ, {"CRON_SECRET": "topsecret"}):
            bad = await client.get("/api/cron/reminders",
                                   headers={"authorization": "Bearer wrong"})
            good = await client.get("/api/cron/reminders",
                                    headers={"authorization": "Bearer topsecret"})
        assert bad.status_code == 401
        assert good.status_code == 200
        assert good.json()["status"] == "ok"
