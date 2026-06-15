"""Bay Coach tests — pure logic, no external calls."""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api


OIL = next(r for r in engine.DEFAULT_RULES if r.name == "Oil & filter change")  # 5000 mi


# ── single-rule evaluation ──────────────────────────────────────────────────────

def test_due_at_interval():
    v = engine.Vehicle(current_mileage=10_000,
                       history=[engine.ServiceRecord("Oil & filter change", 5_000)])
    rec = engine.evaluate_rule(v, OIL)
    assert rec.status == "due"
    assert rec.miles_since_last == 5_000


def test_overdue_past_grace():
    v = engine.Vehicle(current_mileage=11_500,
                       history=[engine.ServiceRecord("Oil & filter change", 5_000)])
    rec = engine.evaluate_rule(v, OIL)
    assert rec.status == "overdue"


def test_upcoming_near_due():
    v = engine.Vehicle(current_mileage=9_500,
                       history=[engine.ServiceRecord("Oil & filter change", 5_000)])
    rec = engine.evaluate_rule(v, OIL)   # 500 mi until due, within 15% of 5000
    assert rec.status == "upcoming"


def test_ok_when_recent():
    v = engine.Vehicle(current_mileage=6_000,
                       history=[engine.ServiceRecord("Oil & filter change", 5_000)])
    rec = engine.evaluate_rule(v, OIL)
    assert rec.status == "ok"


def test_never_recorded_uses_current_mileage():
    v = engine.Vehicle(current_mileage=8_000, history=[])
    rec = engine.evaluate_rule(v, OIL)
    assert rec.status == "overdue"
    assert rec.last_mileage is None
    assert "No record on file" in rec.reason


def test_latest_record_wins():
    v = engine.Vehicle(current_mileage=12_000, history=[
        engine.ServiceRecord("Oil & filter change", 5_000),
        engine.ServiceRecord("Oil & filter change", 10_000),
    ])
    rec = engine.evaluate_rule(v, OIL)
    assert rec.last_mileage == 10_000
    assert rec.miles_since_last == 2_000
    assert rec.status == "ok"


def test_service_name_match_case_insensitive():
    v = engine.Vehicle(current_mileage=6_000,
                       history=[engine.ServiceRecord("oil & FILTER change", 5_000)])
    assert engine.evaluate_rule(v, OIL).status == "ok"


# ── full recommendation set ──────────────────────────────────────────────────────

def test_recommend_ranks_overdue_first():
    v = engine.Vehicle(current_mileage=68_400, year=2019, make="Toyota", model="Camry",
                       history=[
                           engine.ServiceRecord("Oil & filter change", 62_000),
                           engine.ServiceRecord("Transmission fluid", 0),
                       ])
    result = engine.recommend(v)
    assert result["recommendations"][0].priority == 3      # most urgent first
    assert result["overdue_count"] >= 1
    # transmission fluid (60k interval, never since 0) should be actionable
    assert any(r.service == "Transmission fluid" for r in result["actionable"])


def test_render_writeup_runs():
    v = engine.Vehicle(current_mileage=68_400,
                       history=[engine.ServiceRecord("Oil & filter change", 62_000)])
    text = engine.render_writeup_text(engine.recommend(v))
    assert "BAY COACH" in text


def test_up_to_date_vehicle():
    # recently serviced across the board at 50k, now at 50,100
    hist = [engine.ServiceRecord(r.name, 50_000) for r in engine.DEFAULT_RULES]
    v = engine.Vehicle(current_mileage=50_100, history=hist)
    result = engine.recommend(v)
    assert result["overdue_count"] == 0
    assert result["due_count"] == 0


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["rules"] > 0


def test_api_recommend():
    r = client.post("/api/recommend", json={
        "current_mileage": 68_400, "year": 2019, "make": "Toyota", "model": "Camry",
        "history": [{"service": "Oil & filter change", "mileage": 62_000}],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["vehicle"]["current_mileage"] == 68_400
    assert "BAY COACH" in body["writeup_text"]
    assert isinstance(body["actionable"], list)


def test_api_rejects_negative_mileage():
    r = client.post("/api/recommend", json={"current_mileage": -1})
    assert r.status_code == 422
