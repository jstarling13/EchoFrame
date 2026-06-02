"""Clear Ledger tests — pure logic, sender mocked, no external calls."""

import os
import sys
from datetime import date, timedelta

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api

TODAY = date(2026, 6, 2)


def _inv(due_offset, **kw):
    return engine.Invoice(
        kw.pop("invoice_id", "INV1"), kw.pop("customer_name", "Dana Reeves"),
        kw.pop("amount", 1800.0), TODAY + timedelta(days=due_offset), **kw,
    )


# ── dunning timing ───────────────────────────────────────────────────────────

def test_not_due_no_action():
    assert engine.next_action(_inv(+5), today=TODAY) is None


def test_first_reminder_at_one_day_overdue():
    a = engine.next_action(_inv(-1), today=TODAY)
    assert a is not None and a.kind == "reminder" and a.step == 1


def test_paid_invoice_no_action():
    assert engine.next_action(_inv(-30, status="paid"), today=TODAY) is None


def test_final_notice_message_tone():
    # 4th milestone is 30 days overdue
    a = engine.next_action(_inv(-30, reminders_sent=3), today=TODAY)
    assert a.step == 4
    assert "final notice" in a.message.lower()


def test_handoff_after_all_reminders():
    a = engine.next_action(_inv(-31, reminders_sent=4), today=TODAY)
    assert a is not None and a.kind == "handoff"


def test_no_double_send_same_day():
    inv = _inv(-1)
    sender = engine._mock_sender_factory()
    r1 = engine.run_cycle([inv], today=TODAY, sender=sender)
    assert r1["reminders_sent"] == 1
    r2 = engine.run_cycle([inv], today=TODAY, sender=sender)   # still 1 day overdue
    assert r2["reminders_sent"] == 0


# ── AR aging ───────────────────────────────────────────────────────────────────

def test_aging_buckets():
    assert engine.aging_bucket(0) == "current"
    assert engine.aging_bucket(15) == "1-30"
    assert engine.aging_bucket(45) == "31-60"
    assert engine.aging_bucket(90) == "60+"


def test_ar_summary_totals_and_buckets():
    invoices = [
        _inv(+5, amount=600),                 # current
        _inv(-10, amount=950),                # 1-30
        _inv(-45, amount=4200),               # 31-60
        _inv(-20, amount=300, status="paid"), # excluded
    ]
    s = engine.ar_summary(invoices, today=TODAY)
    assert s["open_invoice_count"] == 3
    assert s["total_outstanding"] == 600 + 950 + 4200
    assert s["aging"]["current"] == 600
    assert s["aging"]["1-30"] == 950
    assert s["aging"]["31-60"] == 4200


# ── full sequence ────────────────────────────────────────────────────────────

def test_full_sequence_then_handoff():
    inv = _inv(0)   # due today
    sender = engine._mock_sender_factory()
    handoff_seen = False
    for d in range(0, 40):
        r = engine.run_cycle([inv], today=TODAY + timedelta(days=d), sender=sender)
        if r["handoffs"]:
            handoff_seen = True
            break
    assert inv.reminders_sent == len(engine.DEFAULT_DUNNING_DAYS)
    assert len(sender.sent) == len(engine.DEFAULT_DUNNING_DAYS)
    assert handoff_seen


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_run_cycle():
    r = client.post("/api/run-cycle", json={
        "today": "2026-06-02",
        "invoices": [
            {"invoice_id": "INV-201", "customer_name": "Dana Reeves",
             "amount": 1800, "due_date": "2026-05-31"},
        ],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["reminders_sent"] == 1
    assert body["ar_summary"]["total_outstanding"] == 1800
    assert body["updated_invoices"][0]["reminders_sent"] == 1


def test_api_ar_summary_endpoint():
    r = client.post("/api/ar-summary", json={
        "today": "2026-06-02",
        "invoices": [
            # due 2026-05-20 → 13 days overdue on 2026-06-02 → 1-30 bucket
            {"invoice_id": "INV-1", "customer_name": "X", "amount": 500, "due_date": "2026-05-20"},
        ],
    })
    assert r.status_code == 200
    assert r.json()["aging"]["1-30"] == 500


def test_api_rejects_bad_status():
    r = client.post("/api/run-cycle", json={
        "invoices": [{"invoice_id": "INV-1", "customer_name": "X", "amount": 10,
                      "due_date": "2026-05-01", "status": "void"}],
    })
    assert r.status_code == 422
