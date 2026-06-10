"""
Rate Watch — FastAPI wrapper
─────────────────────────────────────────────────────────────────────────────
Thin HTTP surface over engine.py. No external calls.

Run:  uvicorn api:app --reload --port 8011
Then: POST /api/analyze  with a JSON body of vendors (see README.md).
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Rate Watch", version="0.1.0")


class VendorIn(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=120)
    monthly_cost: float = Field(..., ge=0)
    renewal_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class AnalyzeIn(BaseModel):
    vendors: list[VendorIn]
    renewal_window_days: int = Field(engine.DEFAULT_RENEWAL_WINDOW_DAYS, ge=0, le=365)


def _finding_to_dict(f: engine.VendorFinding) -> dict:
    return {
        "name": f.name, "category": f.category, "monthly_cost": f.monthly_cost,
        "market_typical": f.market_typical, "market_high": f.market_high,
        "overpay_monthly": f.overpay_monthly, "overpay_pct": f.overpay_pct,
        "status": f.status,
        "renewal_date": f.renewal_date.isoformat() if f.renewal_date else None,
        "days_to_renewal": f.days_to_renewal, "renewal_soon": f.renewal_soon,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "categories": len(engine.MARKET_RATES)}


@app.get("/api/categories")
def categories() -> dict:
    return {
        "categories": {
            k: {"low": v[0], "typical": v[1], "high": v[2]}
            for k, v in engine.MARKET_RATES.items()
        }
    }


@app.post("/api/analyze")
def analyze(payload: AnalyzeIn) -> dict:
    vendors = [
        engine.Vendor(
            name=v.name, category=v.category, monthly_cost=v.monthly_cost,
            renewal_date=engine.parse_renewal_date(v.renewal_date),
        )
        for v in payload.vendors
    ]
    report = engine.analyze_vendors(
        vendors, today=date.today(), renewal_window_days=payload.renewal_window_days
    )
    return {
        "generated": report["generated"],
        "vendor_count": report["vendor_count"],
        "overpayer_count": report["overpayer_count"],
        "total_monthly_overpay": report["total_monthly_overpay"],
        "total_annual_overpay": report["total_annual_overpay"],
        "findings": [_finding_to_dict(f) for f in report["findings"]],
        "overpayers": [_finding_to_dict(f) for f in report["overpayers"]],
        "renewals_due": [_finding_to_dict(f) for f in report["renewals_due"]],
        "report_text": engine.render_report_text(report),
    }
