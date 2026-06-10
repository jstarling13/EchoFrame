"""Permit Watch tests — pure logic, no external calls."""

import os
import sys
from datetime import date, timedelta

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api

TODAY = date(2026, 6, 2)


def _item(days, **kw):
    return engine.ComplianceItem(
        kw.pop("name", "Reg"), kw.pop("category", "registration"),
        TODAY + timedelta(days=days), **kw,
    )


# ── status thresholds ───────────────────────────────────────────────────────────

def test_expired():
    s = engine.evaluate_item(_item(-1), today=TODAY)
    assert s.status == "expired"
    assert s.alert is True
    assert s.days_to_expiry == -1


def test_critical_within_7_days():
    s = engine.evaluate_item(_item(5), today=TODAY)
    assert s.status == "critical"
    assert s.alert is True


def test_due_soon_within_window():
    s = engine.evaluate_item(_item(20), today=TODAY)
    assert s.status == "due_soon"
    assert s.alert is True


def test_upcoming_not_alerted():
    s = engine.evaluate_item(_item(45), today=TODAY)
    assert s.status == "upcoming"
    assert s.alert is False


def test_ok_far_out():
    s = engine.evaluate_item(_item(200), today=TODAY)
    assert s.status == "ok"
    assert s.alert is False


def test_custom_window_changes_alert():
    # 45 days: not alerted at 30-day window, alerted at 60-day window
    assert engine.evaluate_item(_item(45), today=TODAY, alert_window=30).alert is False
    assert engine.evaluate_item(_item(45), today=TODAY, alert_window=60).alert is True


# ── dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_sorted_and_grouped():
    items = [
        _item(200, name="Far", entity="Van 9"),
        _item(-3, name="Lapsed", entity="Van 12"),
        _item(5, name="Soon", entity="Truck 3"),
    ]
    db = engine.build_dashboard(items, today=TODAY)
    # most urgent first
    assert db["items"][0].name == "Lapsed"
    assert db["items"][1].name == "Soon"
    assert len(db["alerts"]) == 2
    assert len(db["expired"]) == 1
    assert set(db["by_entity"].keys()) == {"Van 9", "Van 12", "Truck 3"}
    assert db["counts"]["expired"] == 1


def test_business_wide_grouping_for_no_entity():
    db = engine.build_dashboard([_item(10, name="License", category="license")], today=TODAY)
    assert "Business-wide" in db["by_entity"]


def test_digest_renders_expired_and_soon():
    db = engine.build_dashboard(
        [_item(-2, name="Reg", entity="Van 12"), _item(4, name="Inspection", entity="Truck 3")],
        today=TODAY,
    )
    text = engine.render_alert_digest(db)
    assert "EXPIRED" in text
    assert "EXPIRING SOON" in text
    assert "Van 12" in text


def test_digest_all_clear():
    db = engine.build_dashboard([_item(300, name="Reg")], today=TODAY)
    text = engine.render_alert_digest(db)
    assert "All tracked items are current" in text


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_dashboard():
    # Use dates relative to the real "today" so the test is clock-independent:
    # one already expired, one far in the future.
    today = date.today()
    expired_date = (today - timedelta(days=2)).isoformat()
    future_date = (today + timedelta(days=300)).isoformat()
    r = client.post("/api/dashboard", json={
        "items": [
            {"name": "Vehicle registration", "category": "registration",
             "expiry_date": expired_date, "entity": "Van 12"},
            {"name": "Business license", "category": "license",
             "expiry_date": future_date},
        ]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["item_count"] == 2
    assert len(body["expired"]) == 1
    assert "PERMIT WATCH" in body["alert_digest"]


def test_api_rejects_bad_window():
    r = client.post("/api/dashboard", json={
        "items": [{"name": "X", "category": "license", "expiry_date": "2026-07-01"}],
        "alert_window_days": 0,
    })
    assert r.status_code == 422
