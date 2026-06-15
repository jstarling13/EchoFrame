"""Call Catch tests — pure logic, sender mocked, no external calls."""

import os
import sys
from datetime import datetime, time

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api


# ── after-hours detection ───────────────────────────────────────────────────

def test_business_hours_weekday_midday():
    # Tue 2026-06-02 10:30 → open
    assert engine.is_after_hours(datetime(2026, 6, 2, 10, 30)) is False


def test_after_hours_weekday_evening():
    assert engine.is_after_hours(datetime(2026, 6, 2, 19, 45)) is True


def test_weekend_is_after_hours():
    # Sat 2026-06-06 13:00 → closed
    assert engine.is_after_hours(datetime(2026, 6, 6, 13, 0)) is True


def test_boundary_open_inclusive_close_exclusive():
    assert engine.is_after_hours(datetime(2026, 6, 2, 8, 0)) is False    # exactly open
    assert engine.is_after_hours(datetime(2026, 6, 2, 17, 0)) is True    # exactly close


# ── message composition ─────────────────────────────────────────────────────

def test_message_uses_business_name_and_context():
    biz = engine.compose_message("Acme Co", after_hours=False)
    assert "Acme Co" in biz
    after = engine.compose_message("Acme Co", after_hours=True)
    assert "Acme Co" in after
    assert biz != after


# ── handling missed calls ─────────────────────────────────────────────────────

def test_missed_call_sends_text():
    cc = engine.CallCatch("Acme Co")
    e = cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 0))
    assert e.delivered is True
    assert "Acme Co" in e.message_sent
    assert len(cc.sender.sent) == 1


def test_dedupe_repeat_caller_not_texted_twice():
    cc = engine.CallCatch("Acme Co")
    cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 0))
    e2 = cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 2))
    assert e2.delivered is False               # deduped
    assert len(cc.sender.sent) == 1            # only one text total
    assert len(cc.log) == 2                    # but both calls are logged


def test_dedupe_can_be_disabled():
    cc = engine.CallCatch("Acme Co")
    cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 0))
    e2 = cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 2), dedupe=False)
    assert e2.delivered is True
    assert len(cc.sender.sent) == 2


def test_after_hours_template_selected():
    cc = engine.CallCatch("Acme Co")
    e = cc.handle_missed_call("+15550009", occurred_at=datetime(2026, 6, 2, 21, 0))
    assert e.after_hours is True


def test_dashboard_counts():
    cc = engine.CallCatch("Acme Co")
    cc.handle_missed_call("+1", occurred_at=datetime(2026, 6, 2, 10, 0))   # bh
    cc.handle_missed_call("+2", occurred_at=datetime(2026, 6, 2, 20, 0))   # ah
    cc.handle_missed_call("+1", occurred_at=datetime(2026, 6, 2, 10, 5))   # dup
    db = cc.dashboard()
    assert db["total_missed_calls"] == 3
    assert db["texts_sent"] == 2
    assert db["after_hours_calls"] == 1
    assert db["unique_callers"] == 2


def test_custom_template_used():
    cc = engine.CallCatch("Acme Co", templates={
        "business_hours": "BH {business}", "after_hours": "AH {business}",
    })
    e = cc.handle_missed_call("+15550001", occurred_at=datetime(2026, 6, 2, 10, 0))
    assert e.message_sent == "BH Acme Co"


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_missed_call_and_dashboard():
    r = client.post("/webhook/missed-call", json={
        "caller_number": "+17065550101", "occurred_at": "2026-06-02T10:30:00",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["delivered"] is True
    assert body["after_hours"] is False

    d = client.get("/api/dashboard")
    assert d.status_code == 200
    assert d.json()["total_missed_calls"] >= 1
