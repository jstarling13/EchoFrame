"""
Tests for the Quote Revive WEEKLY digest (weekly_quote_revive.py).

Fully offline: ANTHROPIC_API_KEY is removed so messages use the deterministic
template path; resend is stubbed; the store uses its in-memory backend.
"""
import sys
import types

import pytest

# Stub resend so send_digest never hits the network.
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

import store                       # noqa: E402
import weekly_quote_revive as wqr  # noqa: E402

NOW = 1_750_000_000

CSV = (
    "_Business Name,Bayside Plumbing\n"
    "_Owner Name,Sam\n"
    "Quote,Detail,Value,Days Cold,Followups,Status\n"
    "Q-101,Water heater install,2400,3,0,active\n"
    "Q-102,Repipe job,8800,9,1,warm\n"
    "Q-103,Drain cleaning,450,40,2,active\n"
    "Q-104,Bathroom remodel,15000,6,0,active\n"
    "Q-105,Old job,1200,12,3,dead\n"
    "Q-106,Won job,3000,1,1,won\n"
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    # Force the deterministic template messages (no Claude / no network).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _sent.clear()
    if not store.is_configured():
        store._mem.clear(); store._mem_sets.clear()
    yield
    if not store.is_configured():
        store._mem.clear(); store._mem_sets.clear()


def test_digest_selects_open_quotes_top3_by_value():
    d = wqr.build_digest(CSV, "Sam", 0, NOW)
    assert d["call"]["quote"] == "Q-104"          # biggest open opportunity = the one to call
    # Written follow-ups = next biggest open quotes, EXCLUDING the call pick (no
    # point texting a quote we just told you to phone). won/dead excluded too.
    assert [i["quote"] for i in d["items"]] == ["Q-102", "Q-101", "Q-103"]
    assert d["open_count"] == 4                    # Q-101..104 open; Q-105 dead, Q-106 won
    assert all(i.get("message") for i in d["items"])


def test_touch_escalates_with_weeks():
    t0 = {i["quote"]: i["touch_no"] for i in wqr.build_digest(CSV, "Sam", 0, NOW)["items"]}
    assert t0["Q-101"] == 1 and t0["Q-102"] == 2   # 3 days → touch 1, 9 days → touch 2
    t1 = {i["quote"]: i["touch_no"] for i in wqr.build_digest(CSV, "Sam", 1, NOW)["items"]}
    assert t1["Q-101"] == 2 and t1["Q-102"] == 3   # +7 days each → escalated


def test_render_email_has_content():
    html = wqr.render_email(wqr.build_digest(CSV, "Sam", 0, NOW))
    assert "chase list" in html.lower()
    assert "Q-104" in html and "$15,000" in html


def test_run_weekly_sends_one_email():
    store.save_quote_data("sam_at_bayside_com", "sam@bayside.com", CSV, "Sam", NOW)
    summary = wqr.run_weekly(_now=NOW)
    assert summary == {"checked": 1, "sent": 1, "skipped": 0, "errors": 0}
    assert len(_sent) == 1
    assert _sent[0]["to"] == ["sam@bayside.com"]
    assert "chase list" in _sent[0]["subject"].lower()


def test_run_weekly_skips_when_no_open_quotes():
    # All-closed list → no digest to send.
    closed = ("_Business Name,Done Co\nQuote,Detail,Value,Days Cold,Followups,Status\n"
              "Q-1,job,500,5,1,won\nQ-2,job,800,9,2,dead\n")
    store.save_quote_data("d_at_done_com", "d@done.com", closed, "D", NOW)
    summary = wqr.run_weekly(_now=NOW)
    assert summary["sent"] == 0 and summary["checked"] == 1
    assert _sent == []
