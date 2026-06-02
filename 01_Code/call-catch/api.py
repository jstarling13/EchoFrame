"""
Call Catch — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8017

Simulates the telephony webhook: POST /webhook/missed-call with a caller number.
No real texts are sent — the sender is an in-memory mock recorder. State (log) is
kept in-process for the MVP.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Call Catch", version="0.1.0")

# One in-process instance for the demo API. In production this is per-tenant + persisted.
catcher = engine.CallCatch(business_name="Reliable Heating & Air")


class MissedCallIn(BaseModel):
    caller_number: str = Field(..., max_length=40)
    occurred_at: Optional[str] = Field(None, description="ISO datetime; defaults to now")
    dedupe: bool = True


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "business": catcher.business_name}


@app.post("/webhook/missed-call")
def missed_call(payload: MissedCallIn) -> dict:
    occurred = datetime.fromisoformat(payload.occurred_at) if payload.occurred_at else None
    event = catcher.handle_missed_call(
        payload.caller_number, occurred_at=occurred, dedupe=payload.dedupe
    )
    return {
        "caller_number": event.caller_number,
        "occurred_at": event.occurred_at.isoformat(),
        "after_hours": event.after_hours,
        "message_sent": event.message_sent,
        "delivered": event.delivered,
    }


@app.get("/api/dashboard")
def dashboard() -> dict:
    db = catcher.dashboard()
    return {
        "business": db["business"],
        "total_missed_calls": db["total_missed_calls"],
        "texts_sent": db["texts_sent"],
        "after_hours_calls": db["after_hours_calls"],
        "unique_callers": db["unique_callers"],
        "log": [
            {"caller_number": e.caller_number, "occurred_at": e.occurred_at.isoformat(),
             "after_hours": e.after_hours, "delivered": e.delivered}
            for e in db["log"]
        ],
    }
