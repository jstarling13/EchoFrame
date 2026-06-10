"""
Bay Coach — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8014
No external calls.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Bay Coach", version="0.1.0")


class RecordIn(BaseModel):
    service: str = Field(..., max_length=120)
    mileage: int = Field(..., ge=0)
    performed_on: Optional[str] = None


class VehicleIn(BaseModel):
    current_mileage: int = Field(..., ge=0)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    make: Optional[str] = Field(None, max_length=60)
    model: Optional[str] = Field(None, max_length=60)
    history: list[RecordIn] = Field(default_factory=list)


def _rec_to_dict(r: engine.Recommendation) -> dict:
    return {
        "service": r.service, "status": r.status, "reason": r.reason,
        "miles_since_last": r.miles_since_last, "miles_until_due": r.miles_until_due,
        "last_mileage": r.last_mileage, "priority": r.priority,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "rules": len(engine.DEFAULT_RULES)}


@app.post("/api/recommend")
def recommend(payload: VehicleIn) -> dict:
    history = [
        engine.ServiceRecord(
            service=h.service, mileage=h.mileage,
            performed_on=date.fromisoformat(h.performed_on) if h.performed_on else None,
        )
        for h in payload.history
    ]
    vehicle = engine.Vehicle(
        current_mileage=payload.current_mileage, history=history,
        year=payload.year, make=payload.make, model=payload.model,
    )
    result = engine.recommend(vehicle, today=date.today())
    return {
        "vehicle": result["vehicle"],
        "overdue_count": result["overdue_count"],
        "due_count": result["due_count"],
        "recommendations": [_rec_to_dict(r) for r in result["recommendations"]],
        "actionable": [_rec_to_dict(r) for r in result["actionable"]],
        "writeup_text": engine.render_writeup_text(result),
    }
