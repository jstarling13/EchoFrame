"""Rate Watch tests — pure logic, no external calls."""

import os
import sys
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api


# ── engine: single-vendor benchmarking ────────────────────────────────────────

def test_overpayer_detected():
    v = engine.Vendor("X", "merchant processing", 980.0)
    f = engine.analyze_vendor(v)
    assert f.status == "over"
    assert f.overpay_monthly == pytest.approx(980.0 - 450.0)
    assert f.overpay_pct > 0


def test_within_band():
    v = engine.Vendor("X", "payroll software", 80.0)
    f = engine.analyze_vendor(v)
    assert f.status == "within"


def test_under_band():
    v = engine.Vendor("X", "internet", 50.0)
    f = engine.analyze_vendor(v)
    assert f.status == "under"


def test_unknown_category_no_benchmark():
    v = engine.Vendor("X", "quantum widgets", 500.0)
    f = engine.analyze_vendor(v)
    assert f.status == "no_benchmark"
    assert f.overpay_monthly is None


def test_category_is_case_insensitive():
    v = engine.Vendor("X", "  Merchant Processing ", 980.0)
    assert engine.analyze_vendor(v).status == "over"


# ── renewal alerts ─────────────────────────────────────────────────────────────

def test_renewal_soon_flagged():
    today = date(2026, 6, 2)
    v = engine.Vendor("X", "internet", 150.0, renewal_date=today + timedelta(days=10))
    f = engine.analyze_vendor(v, today=today)
    assert f.renewal_soon is True
    assert f.days_to_renewal == 10


def test_renewal_far_out_not_flagged():
    today = date(2026, 6, 2)
    v = engine.Vendor("X", "internet", 150.0, renewal_date=today + timedelta(days=120))
    f = engine.analyze_vendor(v, today=today)
    assert f.renewal_soon is False


def test_past_renewal_not_flagged_as_soon():
    today = date(2026, 6, 2)
    v = engine.Vendor("X", "internet", 150.0, renewal_date=today - timedelta(days=5))
    f = engine.analyze_vendor(v, today=today)
    assert f.renewal_soon is False
    assert f.days_to_renewal == -5


# ── aggregate report ───────────────────────────────────────────────────────────

def test_report_ranks_and_totals():
    today = date(2026, 6, 2)
    vendors = [
        engine.Vendor("Big", "merchant processing", 980.0),   # +530
        engine.Vendor("Small", "pest control", 120.0),        # +30
        engine.Vendor("Fair", "payroll software", 80.0),      # within
    ]
    report = engine.analyze_vendors(vendors, today=today)
    assert report["overpayer_count"] == 2
    # ranked: largest gap first
    assert report["overpayers"][0].name == "Big"
    assert report["total_monthly_overpay"] == pytest.approx(530.0 + 30.0)
    assert report["total_annual_overpay"] == pytest.approx((530.0 + 30.0) * 12)


def test_render_text_runs():
    report = engine.analyze_vendors([engine.Vendor("Big", "internet", 300.0)],
                                    today=date(2026, 6, 2))
    text = engine.render_report_text(report)
    assert "RATE WATCH" in text
    assert "Big" in text


# ── API ─────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_analyze():
    r = client.post("/api/analyze", json={
        "vendors": [
            {"name": "FirstData", "category": "merchant processing", "monthly_cost": 980,
             "renewal_date": "2026-06-15"},
            {"name": "Gusto", "category": "payroll software", "monthly_cost": 75},
        ]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["vendor_count"] == 2
    assert body["overpayer_count"] == 1
    assert body["overpayers"][0]["name"] == "FirstData"
    assert "RATE WATCH" in body["report_text"]


def test_api_rejects_negative_cost():
    r = client.post("/api/analyze", json={
        "vendors": [{"name": "X", "category": "internet", "monthly_cost": -5}]
    })
    assert r.status_code == 422
