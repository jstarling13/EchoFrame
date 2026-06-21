"""
Quote Revive digest: the call-pick is never duplicated as a written message, and
the digest is routed through the owner-approval gate (not sent straight to the
client) when REVIEW_MODE is on.
"""
import pytest


def test_call_pick_not_duplicated_as_written_message():
    import weekly_quote_revive as w
    csv = ("_Business Name,Acme\n"
           "Quote,Detail,Value,Days Cold,Followups,Status\n"
           "Q1,Big job,5000,3,0,active\n"
           "Q2,Small job,500,3,0,active\n"
           "Q3,Mid job,1500,3,0,active\n")
    d = w.build_digest(csv, "Sam", 0, 1781900000)
    assert d["call"]["quote"] == "Q1"                       # biggest = the one to call
    written = [it["quote"] for it in d["items"]]
    assert "Q1" not in written                              # not ALSO a written follow-up
    assert set(written) == {"Q2", "Q3"}


def test_digest_is_held_for_owner_review(monkeypatch):
    import resend, email_failsafe, review_gate
    sent = []
    def fake_send(params, *a, **k):
        sent.append(params)
        return {"id": "stub"}
    monkeypatch.setattr(resend.Emails, "send", fake_send, raising=False)
    monkeypatch.setenv("REVIEW_MODE", "on")
    monkeypatch.setenv("ALERT_EMAIL", "owner@echoframe.net")
    monkeypatch.setenv("EMAIL_FROM", "EchoFrame <owner@echoframe.net>")
    monkeypatch.setenv("RESEND_API_KEY", "test")
    # Install failsafe then the review gate over the stub (production install order).
    email_failsafe.install()
    review_gate.install()

    import weekly_quote_revive as w
    digest = {"owner": "Sam", "biz": "Acme", "week_label": "Week of X",
              "open_count": 1, "open_value": "$1,000",
              "items": [], "call": None, "flagged": []}
    w.send_digest("client@biz.com", digest)

    tos = [t for p in sent for t in (p.get("to") or [])]
    assert "client@biz.com" not in tos                      # client did NOT get it directly
    assert any("owner@echoframe.net" in str(t) for t in tos)  # owner got the review copy
    assert any(str(p.get("subject", "")).startswith("[REVIEW]") for p in sent)


def test_digest_sends_directly_when_review_off(monkeypatch):
    import resend, email_failsafe, review_gate
    sent = []
    monkeypatch.setattr(resend.Emails, "send", lambda params, *a, **k: sent.append(params),
                        raising=False)
    monkeypatch.setenv("REVIEW_MODE", "off")
    monkeypatch.setenv("RESEND_API_KEY", "test")
    email_failsafe.install()
    review_gate.install()

    import weekly_quote_revive as w
    digest = {"owner": "Sam", "biz": "Acme", "week_label": "Week of X",
              "open_count": 1, "open_value": "$1,000",
              "items": [], "call": None, "flagged": []}
    w.send_digest("client@biz.com", digest)
    tos = [t for p in sent for t in (p.get("to") or [])]
    assert tos == ["client@biz.com"]                        # gate off → straight to client
