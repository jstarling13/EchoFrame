"""Shift Lens tests — pure logic, no external calls."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api


# ── labor cost resolution ──────────────────────────────────────────────────────

def test_labor_cost_from_hours_and_wage():
    s = engine.Shift("X", revenue=1000, labor_hours=20, avg_wage=15)
    assert s.resolved_labor_cost() == 300.0


def test_labor_cost_direct_takes_precedence():
    s = engine.Shift("X", revenue=1000, labor_cost=250, labor_hours=20, avg_wage=15)
    assert s.resolved_labor_cost() == 250.0


def test_missing_labor_inputs_raises():
    with pytest.raises(ValueError):
        engine.Shift("X", revenue=1000).resolved_labor_cost()


# ── classification ──────────────────────────────────────────────────────────────

def test_healthy_shift():
    r = engine.analyze_shift(engine.Shift("X", revenue=1000, labor_cost=250))
    assert r.status == "healthy"
    assert r.labor_pct == 25.0
    assert r.contribution == 750.0


def test_watch_shift_just_over_target():
    r = engine.analyze_shift(engine.Shift("X", revenue=1000, labor_cost=350))
    assert r.status == "watch"


def test_underperforming_well_over_target():
    r = engine.analyze_shift(engine.Shift("X", revenue=1000, labor_cost=500))
    assert r.status == "underperforming"


def test_loss_making_shift():
    r = engine.analyze_shift(engine.Shift("X", revenue=300, labor_cost=420))
    assert r.status == "underperforming"
    assert r.contribution == -120.0


def test_no_revenue_shift():
    r = engine.analyze_shift(engine.Shift("X", revenue=0, labor_cost=100))
    assert r.status == "no_revenue"
    assert r.labor_pct is None


def test_custom_target_changes_classification():
    # 28% labor is healthy at 30% target, but a watch at 25% target
    assert engine.analyze_shift(engine.Shift("X", 1000, labor_cost=280),
                                target_labor_pct=30).status == "healthy"
    assert engine.analyze_shift(engine.Shift("X", 1000, labor_cost=280),
                                target_labor_pct=25).status == "watch"


# ── weekly report ────────────────────────────────────────────────────────────────

def test_week_totals_and_ranking():
    shifts = [
        engine.Shift("Good", revenue=5000, labor_cost=1250),   # +3750
        engine.Shift("Bad", revenue=300, labor_cost=420),      # -120
        engine.Shift("Mid", revenue=1000, labor_cost=300),     # +700
    ]
    report = engine.analyze_week(shifts)
    assert report["shift_count"] == 3
    assert report["total_revenue"] == 6300
    assert report["best_shift"].label == "Good"
    assert report["worst_shift"].label == "Bad"
    assert any(u.label == "Bad" for u in report["underperformers"])


def test_render_text_runs():
    report = engine.analyze_week([engine.Shift("S", 1000, labor_cost=250)])
    text = engine.render_report_text(report)
    assert "SHIFT LENS" in text


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_analyze():
    r = client.post("/api/analyze", json={
        "shifts": [
            {"label": "Sat Dinner", "revenue": 5200, "labor_cost": 1300},
            {"label": "Wed Lunch", "revenue": 300, "labor_cost": 420},
        ]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["shift_count"] == 2
    assert body["worst_shift"]["label"] == "Wed Lunch"
    assert "SHIFT LENS" in body["report_text"]


def test_api_missing_labor_returns_400():
    r = client.post("/api/analyze", json={
        "shifts": [{"label": "X", "revenue": 1000}]
    })
    assert r.status_code == 400


def test_api_rejects_negative_revenue():
    r = client.post("/api/analyze", json={
        "shifts": [{"label": "X", "revenue": -5, "labor_cost": 10}]
    })
    assert r.status_code == 422
