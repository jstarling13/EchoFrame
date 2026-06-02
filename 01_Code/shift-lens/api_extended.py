"""
Shift Lens — Extended API with data ingestion, processing, and reporting.
Run: uvicorn api_extended:app --reload --port 8012
"""

from datetime import datetime, date
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from db import get_db, init_db
from models import SessionLocal
from models.shift_definition import ShiftDefinition
from schemas.input import (
    IngestTransactionsRequest,
    IngestPunchesRequest,
    ProcessDayRequest,
)
from schemas.output import ShiftResultOutput
from service.shift_service import ShiftPLService
from service.aggregations import WeeklyAggregator, ShiftHistoryAnalyzer
import engine

app = FastAPI(title="Shift Lens", version="0.2.0")

def get_service(db: Session = Depends(get_db)) -> ShiftPLService:
    """Inject ShiftPLService with shift definitions."""
    shifts = db.query(ShiftDefinition).all()
    return ShiftPLService(db, shifts)

@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/ingest/transactions")
def ingest_transactions(
    payload: IngestTransactionsRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest raw POS transaction data.

    Example request:
    {
      "location_id": "columbus-main",
      "transactions": [
        {"timestamp": "2024-01-15T14:32:00", "amount": 45.50, "order_id": "ORD-12345", "location_id": "columbus-main"}
      ]
    }
    """
    try:
        service = get_service(db)
        from etl.ingestion import ingest_from_dict
        from models.transaction import POSTransaction
        from decimal import Decimal

        txn_df, _ = ingest_from_dict(
            [t.model_dump() for t in payload.transactions], []
        )
        service.persistence.insert_transactions(txn_df)

        return {
            "status": "ok",
            "count": len(payload.transactions),
            "location_id": payload.location_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/ingest/time-punches")
def ingest_punches(
    payload: IngestPunchesRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest raw labor time punch data.

    Example request:
    {
      "location_id": "columbus-main",
      "time_punches": [
        {"employee_id": "EMP-001", "clock_in": "2024-01-15T06:00:00", "clock_out": "2024-01-15T14:00:00", "location_id": "columbus-main", "wage": 15.00}
      ]
    }
    """
    try:
        service = get_service(db)
        from etl.ingestion import ingest_from_dict

        _, punch_df = ingest_from_dict(
            [], [p.model_dump() for p in payload.time_punches]
        )
        service.persistence.insert_punches(punch_df)

        return {
            "status": "ok",
            "count": len(payload.time_punches),
            "location_id": payload.location_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/process-day")
def process_day(
    payload: ProcessDayRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger full ETL pipeline for a day: ingest → map → allocate → persist → analyze.

    Returns the daily totals and shift-by-shift breakdown.
    """
    try:
        service = get_service(db)
        shift_date = datetime.fromisoformat(payload.date).date()

        totals = service.process_day(
            shift_date=shift_date,
            location_id=payload.location_id,
            raw_transactions=[t.model_dump() for t in payload.transactions],
            raw_punches=[p.model_dump() for p in payload.time_punches],
            target_labor_pct=payload.target_labor_pct,
        )

        weekly = service.get_weekly_report(shift_date, payload.location_id, payload.target_labor_pct)

        return {
            "status": "ok",
            "date": str(shift_date),
            "totals": totals,
            "shift_results": [r.__dict__ for r in weekly["results"]],
            "report_text": weekly["report_text"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/weekly-report/{location_id}")
def weekly_report(
    location_id: str,
    week_start: str,
    target_labor_pct: float = 30.0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Fetch computed weekly P&L report.

    Example: GET /api/weekly-report/columbus-main?week_start=2024-01-15
    """
    try:
        service = get_service(db)
        week_date = datetime.fromisoformat(week_start).date()
        report = service.get_weekly_report(week_date, location_id, target_labor_pct)

        return {
            "status": "ok",
            "week_start": str(week_date),
            "location_id": location_id,
            "shift_results": [r.__dict__ for r in report["results"]],
            "report_text": report["report_text"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/shift-history/{shift_id}")
def shift_history(
    shift_id: int,
    location_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Fetch historical performance for a specific shift.

    Example: GET /api/shift-history/1?location_id=columbus-main&days=30
    """
    try:
        service = get_service(db)
        history = service.get_shift_history(shift_id, location_id, days)

        return {
            "status": "ok",
            "shift_id": shift_id,
            "location_id": location_id,
            "days": days,
            "records": history,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/weekly-aggregate/{location_id}")
def weekly_aggregate(
    location_id: str,
    week_start: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed weekly aggregation (by day breakdown).

    Example: GET /api/weekly-aggregate/columbus-main?week_start=2024-01-15
    """
    try:
        week_date = datetime.fromisoformat(week_start).date()
        aggregator = WeeklyAggregator(db)
        agg = aggregator.aggregate_week(week_date, location_id)

        return {
            "status": "ok",
            **agg,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/initialize-db")
def initialize_database() -> Dict[str, str]:
    """
    Initialize database tables (dev only).
    """
    try:
        init_db()
        return {"status": "ok", "message": "Database tables created."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
