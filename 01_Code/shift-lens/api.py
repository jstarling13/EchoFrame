"""
Shift Lens — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8012
No external calls.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Shift Lens", version="0.1.0")


class ShiftIn(BaseModel):
    label: str = Field(..., max_length=120)
    revenue: float = Field(..., ge=0)
    labor_cost: Optional[float] = Field(None, ge=0)
    labor_hours: Optional[float] = Field(None, ge=0)
    avg_wage: Optional[float] = Field(None, ge=0)


class AnalyzeIn(BaseModel):
    shifts: list[ShiftIn]
    target_labor_pct: float = Field(engine.DEFAULT_TARGET_LABOR_PCT, gt=0, le=100)


def _result_to_dict(r: engine.ShiftResult) -> dict:
    return {
        "label": r.label, "revenue": r.revenue, "labor_cost": r.labor_cost,
        "labor_pct": r.labor_pct, "contribution": r.contribution,
        "status": r.status, "recommendation": r.recommendation,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(payload: AnalyzeIn) -> dict:
    shifts = [
        engine.Shift(label=s.label, revenue=s.revenue, labor_cost=s.labor_cost,
                     labor_hours=s.labor_hours, avg_wage=s.avg_wage)
        for s in payload.shifts
    ]
    try:
        report = engine.analyze_week(shifts, target_labor_pct=payload.target_labor_pct)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "target_labor_pct": report["target_labor_pct"],
        "shift_count": report["shift_count"],
        "total_revenue": report["total_revenue"],
        "total_labor": report["total_labor"],
        "overall_labor_pct": report["overall_labor_pct"],
        "total_contribution": report["total_contribution"],
        "results": [_result_to_dict(r) for r in report["results"]],
        "underperformers": [_result_to_dict(r) for r in report["underperformers"]],
        "best_shift": _result_to_dict(report["best_shift"]) if report["best_shift"] else None,
        "worst_shift": _result_to_dict(report["worst_shift"]) if report["worst_shift"] else None,
        "report_text": engine.render_report_text(report),
    }
