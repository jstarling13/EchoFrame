"""
Fulfillment guard — a paid upload must NEVER end in silence.

These tests prove that when an engine can't read a file (or crashes before it
ever sends), the customer still gets a reassurance email and the owner gets an
alert with the file attached. No network: resend.Emails.send is stubbed.
"""
import pytest


@pytest.fixture
def captured(monkeypatch):
    import resend, email_failsafe
    sent = []
    def fake_send(params, *a, **k):
        sent.append(params)
        return {"id": "stub"}
    monkeypatch.setattr(resend.Emails, "send", fake_send, raising=False)
    # Re-wrap the stub with the real failsafe so the delivery-attempt counter
    # increments exactly as it does in production.
    email_failsafe.install()
    monkeypatch.setenv("RESEND_API_KEY", "test")
    monkeypatch.setenv("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")
    monkeypatch.setenv("FAILSAFE_EMAIL", "owner@example.com")
    return sent


def _tos(sent):
    return [p["to"][0] for p in sent]


def test_notify_unreadable_messages_customer_and_owner(captured):
    import fulfillment_guard
    fulfillment_guard.notify_unreadable("client@biz.com", "Sam", "Quote Revive",
                                        reason="couldn't read file",
                                        raw="a,b,c\n1,2,3\n", filename="x.csv")
    tos = _tos(captured)
    assert "client@biz.com" in tos          # customer reassured
    assert "owner@example.com" in tos       # owner alerted
    owner = next(p for p in captured if p["to"][0] == "owner@example.com")
    assert owner.get("attachments")                                   # file attached
    assert owner["attachments"][0]["content_type"] == "text/csv"


def test_notify_unreadable_never_raises_even_if_send_fails(monkeypatch):
    import resend, fulfillment_guard
    def boom(params, *a, **k):
        raise RuntimeError("resend down")
    monkeypatch.setattr(resend.Emails, "send", boom, raising=False)
    monkeypatch.setenv("RESEND_API_KEY", "test")
    # Must not propagate — a guard that throws defeats its purpose.
    fulfillment_guard.notify_unreadable("c@b.com", "Sam", "Clarity Report", reason="x")


def test_quote_revive_unreadable_file_notifies(captured):
    import weekly_quote_revive as w
    # No recognizable quote columns → build_digest returns None.
    w.send_first_digest("client@biz.com", "just,some\nrandom,text\n", "Sam", 1781900000)
    tos = _tos(captured)
    assert "client@biz.com" in tos and "owner@example.com" in tos


def test_quote_revive_readable_but_empty_still_confirms(captured):
    import weekly_quote_revive as w
    # Readable quotes, but all already closed → nothing to chase. The customer
    # should still get a confirmation, not silence.
    csv = ("_Business Name,Acme\n"
           "Quote,Detail,Value,Days Cold,Followups,Status\n"
           "Q1,Job A,500,3,0,won\n")
    w.send_first_digest("client@biz.com", csv, "Sam", 1781900000)
    assert "client@biz.com" in _tos(captured)


def test_run_report_sync_notifies_when_engine_delivers_nothing(captured):
    import main
    def broken_generate(email, name, fields):
        raise ValueError("couldn't read CSV")
    main._run_report_sync(broken_generate, "client@biz.com", "Sam", {}, "clarity", "Clarity Report")
    tos = _tos(captured)
    assert "client@biz.com" in tos and "owner@example.com" in tos


def test_run_report_sync_stays_quiet_on_success(captured):
    import main, resend
    # An engine that DOES deliver (calls resend) must not trigger the guard.
    def good_generate(email, name, fields):
        resend.Emails.send({"from": "x", "to": ["client@biz.com"], "subject": "r", "html": "<p>ok</p>"})
        return "/tmp/report.html"
    main._run_report_sync(good_generate, "client@biz.com", "Sam", {}, "clarity", "Clarity Report")
    # Exactly one email — the report — and no owner alert.
    assert _tos(captured) == ["client@biz.com"]
