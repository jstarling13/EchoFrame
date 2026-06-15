"""
Quote Revive — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8015
No real messages are sent — the sender is an in-memory mock recorder.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Quote Revive", version="0.1.0")


class QuoteIn(BaseModel):
    quote_id: str = Field(..., max_length=80)
    customer_name: str = Field(..., max_length=200)
    amount: float = Field(..., ge=0)
    sent_date: str = Field(..., description="ISO date YYYY-MM-DD")
    status: str = Field("open", pattern="^(open|accepted|declined)$")
    followups_sent: int = Field(0, ge=0)
    last_contact_date: Optional[str] = None


class CycleIn(BaseModel):
    quotes: list[QuoteIn]
    today: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "schedule_days": engine.DEFAULT_SCHEDULE_DAYS}


@app.post("/api/run-cycle")
def run_cycle(payload: CycleIn) -> dict:
    today = date.fromisoformat(payload.today) if payload.today else date.today()
    quotes = [
        engine.Quote(
            quote_id=q.quote_id, customer_name=q.customer_name, amount=q.amount,
            sent_date=date.fromisoformat(q.sent_date), status=q.status,
            followups_sent=q.followups_sent,
            last_contact_date=date.fromisoformat(q.last_contact_date) if q.last_contact_date else None,
        )
        for q in payload.quotes
    ]
    result = engine.run_cycle(quotes, today=today)
    return {
        "date": result["date"],
        "quotes_processed": result["quotes_processed"],
        "followups_sent": result["followups_sent"],
        "messages": getattr(result["sender"], "sent", []),
        "handoffs": [
            {"quote_id": h.quote_id, "customer_name": h.customer_name, "message": h.message}
            for h in result["handoffs"]
        ],
        "updated_quotes": [
            {"quote_id": q.quote_id, "followups_sent": q.followups_sent,
             "last_contact_date": q.last_contact_date.isoformat() if q.last_contact_date else None}
            for q in quotes
        ],
    }
