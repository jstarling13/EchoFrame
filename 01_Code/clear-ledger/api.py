"""
Clear Ledger — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8016
No real messages are sent — sender is an in-memory mock recorder.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Clear Ledger", version="0.1.0")


class InvoiceIn(BaseModel):
    invoice_id: str = Field(..., max_length=80)
    customer_name: str = Field(..., max_length=200)
    amount: float = Field(..., ge=0)
    due_date: str = Field(..., description="ISO date YYYY-MM-DD")
    status: str = Field("open", pattern="^(open|paid)$")
    reminders_sent: int = Field(0, ge=0)


class CycleIn(BaseModel):
    invoices: list[InvoiceIn]
    today: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "dunning_days": engine.DEFAULT_DUNNING_DAYS}


@app.post("/api/run-cycle")
def run_cycle(payload: CycleIn) -> dict:
    today = date.fromisoformat(payload.today) if payload.today else date.today()
    invoices = [
        engine.Invoice(
            invoice_id=i.invoice_id, customer_name=i.customer_name, amount=i.amount,
            due_date=date.fromisoformat(i.due_date), status=i.status,
            reminders_sent=i.reminders_sent,
        )
        for i in payload.invoices
    ]
    result = engine.run_cycle(invoices, today=today)
    return {
        "date": result["date"],
        "invoices_processed": result["invoices_processed"],
        "reminders_sent": result["reminders_sent"],
        "messages": getattr(result["sender"], "sent", []),
        "handoffs": [
            {"invoice_id": h.invoice_id, "customer_name": h.customer_name,
             "message": h.message, "days_overdue": h.days_overdue}
            for h in result["handoffs"]
        ],
        "ar_summary": result["ar_summary"],
        "updated_invoices": [
            {"invoice_id": i.invoice_id, "reminders_sent": i.reminders_sent}
            for i in invoices
        ],
    }


@app.post("/api/ar-summary")
def ar_summary(payload: CycleIn) -> dict:
    today = date.fromisoformat(payload.today) if payload.today else date.today()
    invoices = [
        engine.Invoice(
            invoice_id=i.invoice_id, customer_name=i.customer_name, amount=i.amount,
            due_date=date.fromisoformat(i.due_date), status=i.status,
            reminders_sent=i.reminders_sent,
        )
        for i in payload.invoices
    ]
    return engine.ar_summary(invoices, today=today)
