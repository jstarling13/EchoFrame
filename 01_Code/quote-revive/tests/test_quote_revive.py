"""Quote Revive tests — pure logic, sender mocked, no external calls."""

import os
import sys
from datetime import date, timedelta

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api

START = date(2026, 6, 2)


def _quote(**kw):
    return engine.Quote(
        kw.pop("quote_id", "Q1"), kw.pop("customer_name", "Dana Reeves"),
        kw.pop("amount", 4800.0), kw.pop("sent_date", START), **kw,
    )


# ── next_action timing ───────────────────────────────────────────────────────

def test_no_action_before_first_interval():
    q = _quote()
    assert engine.next_action(q, today=START + timedelta(days=1)) is None  # interval is 2


def test_first_followup_fires_at_interval():
    q = _quote()
    a = engine.next_action(q, today=START + timedelta(days=2))
    assert a is not None and a.kind == "followup" and a.step == 1


def test_no_action_for_accepted_quote():
    q = _quote(status="accepted")
    assert engine.next_action(q, today=START + timedelta(days=30)) is None


def test_handoff_after_schedule_exhausted():
    q = _quote(followups_sent=4, last_contact_date=START)   # all 4 sent
    a = engine.next_action(q, today=START + timedelta(days=14))
    assert a is not None and a.kind == "handoff"


def test_no_double_send_same_day():
    q = _quote()
    sender = engine._mock_sender_factory()
    r1 = engine.run_cycle([q], today=START + timedelta(days=2), sender=sender)
    assert r1["followups_sent"] == 1
    # same day again → last_contact is today, so nothing due
    r2 = engine.run_cycle([q], today=START + timedelta(days=2), sender=sender)
    assert r2["followups_sent"] == 0


# ── full sequence progression ──────────────────────────────────────────────────

def test_full_sequence_then_handoff():
    q = _quote()
    sender = engine._mock_sender_factory()
    handoff_seen = False
    for offset in range(0, 25):
        r = engine.run_cycle([q], today=START + timedelta(days=offset), sender=sender)
        if r["handoffs"]:
            handoff_seen = True
            break
    assert q.followups_sent == len(engine.DEFAULT_SCHEDULE_DAYS)
    assert len(sender.sent) == len(engine.DEFAULT_SCHEDULE_DAYS)
    assert handoff_seen


def test_run_cycle_updates_state():
    q = _quote()
    sender = engine._mock_sender_factory()
    engine.run_cycle([q], today=START + timedelta(days=2), sender=sender)
    assert q.followups_sent == 1
    assert q.last_contact_date == START + timedelta(days=2)


def test_final_message_is_softer():
    q = _quote(followups_sent=3, last_contact_date=START)
    a = engine.next_action(q, today=START + timedelta(days=14))
    assert a.step == 4
    assert "close it out" in a.message.lower() or "hold it" in a.message.lower()


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_run_cycle_sends_followup():
    r = client.post("/api/run-cycle", json={
        "today": "2026-06-04",
        "quotes": [{
            "quote_id": "Q1", "customer_name": "Dana Reeves",
            "amount": 4800, "sent_date": "2026-06-02",
        }],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["followups_sent"] == 1
    assert len(body["messages"]) == 1
    assert body["updated_quotes"][0]["followups_sent"] == 1


def test_api_rejects_bad_status():
    r = client.post("/api/run-cycle", json={
        "quotes": [{"quote_id": "Q1", "customer_name": "X", "amount": 10,
                    "sent_date": "2026-06-02", "status": "bogus"}],
    })
    assert r.status_code == 422
