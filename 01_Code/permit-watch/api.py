"""
Permit Watch — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8013
No external calls.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Permit Watch", version="0.1.0")


class ItemIn(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=80)
    expiry_date: str = Field(..., description="ISO date YYYY-MM-DD")
    entity: Optional[str] = Field(None, max_length=120)
    identifier: Optional[str] = Field(None, max_length=120)
    notes: Optional[str] = Field(None, max_length=500)


class DashboardIn(BaseModel):
    items: list[ItemIn]
    alert_window_days: int = Field(engine.DEFAULT_ALERT_WINDOW_DAYS, ge=1, le=365)


def _status_to_dict(s: engine.ItemStatus) -> dict:
    return {
        "name": s.name, "category": s.category, "entity": s.entity,
        "identifier": s.identifier, "expiry_date": s.expiry_date.isoformat(),
        "days_to_expiry": s.days_to_expiry, "status": s.status, "alert": s.alert,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/dashboard")
def dashboard(payload: DashboardIn) -> dict:
    items = [
        engine.ComplianceItem(
            name=i.name, category=i.category,
            expiry_date=engine.parse_date(i.expiry_date),
            entity=i.entity, identifier=i.identifier, notes=i.notes,
        )
        for i in payload.items
    ]
    db = engine.build_dashboard(items, today=date.today(),
                                alert_window=payload.alert_window_days)
    return {
        "generated": db["generated"],
        "alert_window_days": db["alert_window_days"],
        "item_count": db["item_count"],
        "counts": db["counts"],
        "items": [_status_to_dict(s) for s in db["items"]],
        "alerts": [_status_to_dict(s) for s in db["alerts"]],
        "expired": [_status_to_dict(s) for s in db["expired"]],
        "by_entity": {
            k: [_status_to_dict(s) for s in v] for k, v in db["by_entity"].items()
        },
        "alert_digest": engine.render_alert_digest(db),
    }
