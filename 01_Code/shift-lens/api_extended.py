"""
Shift Lens — Extended API: connector sync, data ingestion, processing, reporting.
Run: uvicorn api_extended:app --reload --port 8012

Auth: mutating endpoints require header `X-API-Key` to match SHIFT_LENS_API_KEY
when that env var is set. If it is unset (local dev), auth is disabled.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import config
from db import get_db, init_db
from models.shift_definition import ShiftDefinition
from schemas.input import (
    IngestTransactionsRequest,
    IngestPunchesRequest,
    ProcessDayRequest,
    SyncDayRequest,
    PosWebhookRequest,
    PunchWebhookRequest,
)
from service.shift_service import ShiftPLService
from service.aggregations import WeeklyAggregator
from etl.ingestion import ingest_from_dict
from connectors import get_pos_connector, get_timesheet_connector, available_sources
from scheduler import scheduler
from logging_config import get_logger

logger = get_logger("api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Shift Lens API started (auth=%s)", "on" if config.API_KEY else "off")
    scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


app = FastAPI(title="Shift Lens", version="0.3.0", lifespan=lifespan)

# Allow the static EchoFrame site (file:// or localhost) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Reject mutating calls when an API key is configured and not matched."""
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key.")


def build_service(db: Session) -> ShiftPLService:
    """Construct a service bound to the request's session + current shift defs."""
    shifts = db.query(ShiftDefinition).all()
    return ShiftPLService(db, shifts)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    """Send the bare host to the live dashboard."""
    return RedirectResponse(url="/app/dashboard.html")


# Serve the standalone live dashboard (same-origin, so no CORS needed).
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(_STATIC_DIR), html=True), name="app")


@app.get("/api/shifts/{location_id}")
def list_shifts(location_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List configured shift definitions for a location."""
    shifts = (
        db.query(ShiftDefinition)
        .filter(ShiftDefinition.location_id == location_id)
        .order_by(ShiftDefinition.day_of_week, ShiftDefinition.start_time)
        .all()
    )
    return {
        "status": "ok",
        "location_id": location_id,
        "shifts": [
            {
                "id": s.id,
                "shift_name": s.shift_name,
                "day_of_week": s.day_of_week,
                "start_time": str(s.start_time),
                "end_time": str(s.end_time),
            }
            for s in shifts
        ],
    }


@app.post("/api/ingest/transactions")
def ingest_transactions(
    payload: IngestTransactionsRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """Ingest raw POS transaction data."""
    try:
        service = build_service(db)
        txn_df, _df = ingest_from_dict([t.model_dump() for t in payload.transactions], [])
        service.persistence.insert_transactions(txn_df)
        return {"status": "ok", "count": len(payload.transactions), "location_id": payload.location_id}
    except Exception as e:
        logger.exception("ingest_transactions failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ingest/time-punches")
def ingest_punches(
    payload: IngestPunchesRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """Ingest raw labor time punch data."""
    try:
        service = build_service(db)
        _df, punch_df = ingest_from_dict([], [p.model_dump() for p in payload.time_punches])
        service.persistence.insert_punches(punch_df)
        return {"status": "ok", "count": len(payload.time_punches), "location_id": payload.location_id}
    except Exception as e:
        logger.exception("ingest_punches failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/process-day")
def process_day(
    payload: ProcessDayRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """Full ETL for a day from an explicit payload: ingest → map → allocate → persist → analyze."""
    try:
        service = build_service(db)
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
        logger.exception("process_day failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sync-day")
def sync_day(
    payload: SyncDayRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    Pull a day's POS + timesheet data from connectors and run the full pipeline.

    This is the production integration seam: swap `pos_source`/`timesheet_source`
    for real connectors without changing the ETL or service layers.
    """
    try:
        service = build_service(db)
        shift_date = datetime.fromisoformat(payload.date).date()

        pos = get_pos_connector(payload.pos_source)
        timesheet = get_timesheet_connector(payload.timesheet_source)
        transactions = pos.fetch_transactions(shift_date, payload.location_id)
        punches = timesheet.fetch_punches(shift_date, payload.location_id)

        totals = service.process_day(
            shift_date=shift_date,
            location_id=payload.location_id,
            raw_transactions=transactions,
            raw_punches=punches,
            target_labor_pct=payload.target_labor_pct,
        )
        weekly = service.get_weekly_report(shift_date, payload.location_id, payload.target_labor_pct)
        return {
            "status": "ok",
            "date": str(shift_date),
            "sources": {"pos": pos.name, "timesheet": timesheet.name},
            "totals": totals,
            "shift_results": [r.__dict__ for r in weekly["results"]],
            "report_text": weekly["report_text"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("sync_day failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/webhooks/pos")
def webhook_pos(
    payload: PosWebhookRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    Real-time POS event: append a single transaction and recompute its day.

    This is the push counterpart to /api/sync-day — a POS can fire this per sale
    so the shift P&L updates live.
    """
    try:
        service = build_service(db)
        txn = payload.transaction
        shift_date = txn.timestamp.date()
        txn_df, _df = ingest_from_dict([txn.model_dump()], [])
        service.persistence.insert_transactions(txn_df)
        totals = service.recompute_day(shift_date, txn.location_id, payload.target_labor_pct)
        day = service.get_day_report(shift_date, txn.location_id, payload.target_labor_pct)
        return {
            "status": "ok",
            "event": "pos_transaction",
            "date": str(shift_date),
            "totals": totals,
            "shift_results": [r.__dict__ for r in day["results"]],
        }
    except Exception as e:
        logger.exception("webhook_pos failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/webhooks/timesheet")
def webhook_timesheet(
    payload: PunchWebhookRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    """Real-time labor event: append a single punch and recompute its day."""
    try:
        service = build_service(db)
        punch = payload.time_punch
        shift_date = punch.clock_in.date()
        _df, punch_df = ingest_from_dict([], [punch.model_dump()])
        service.persistence.insert_punches(punch_df)
        totals = service.recompute_day(shift_date, punch.location_id, payload.target_labor_pct)
        day = service.get_day_report(shift_date, punch.location_id, payload.target_labor_pct)
        return {
            "status": "ok",
            "event": "time_punch",
            "date": str(shift_date),
            "totals": totals,
            "shift_results": [r.__dict__ for r in day["results"]],
        }
    except Exception as e:
        logger.exception("webhook_timesheet failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sources")
def sources() -> Dict[str, Any]:
    """List connector sources that are usable right now (Square needs a token)."""
    return {"status": "ok", **available_sources()}


@app.get("/api/scheduler")
def scheduler_status() -> Dict[str, Any]:
    """Report auto-sync scheduler configuration/state."""
    return {
        "status": "ok",
        "enabled": config.AUTO_SYNC_ENABLED,
        "interval_seconds": config.AUTO_SYNC_INTERVAL_SECONDS,
        "locations": config.AUTO_SYNC_LOCATIONS,
        "pos_source": config.AUTO_SYNC_POS_SOURCE,
        "timesheet_source": config.AUTO_SYNC_TIMESHEET_SOURCE,
    }


@app.post("/api/sync-now")
def sync_now(_: None = Depends(require_api_key)) -> Dict[str, Any]:
    """Manually trigger one auto-sync pass across configured locations (today)."""
    try:
        summary = scheduler.sync_once()
        return {"status": "ok", "synced": summary}
    except Exception as e:
        logger.exception("sync_now failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/day/{location_id}")
def day_report(
    location_id: str,
    date: str,
    target_labor_pct: float = 30.0,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Read a single day's stored P&L (used by the live dashboard polling loop)."""
    try:
        service = build_service(db)
        shift_date = datetime.fromisoformat(date).date()
        day = service.get_day_report(shift_date, location_id, target_labor_pct)
        rd = day["report_dict"]
        return {
            "status": "ok",
            "date": day["date"],
            "location_id": location_id,
            "totals": {
                "total_revenue": rd["total_revenue"],
                "total_labor": rd["total_labor"],
                "overall_labor_pct": rd["overall_labor_pct"],
                "total_contribution": rd["total_contribution"],
            },
            "shift_results": [r.__dict__ for r in day["results"]],
            "report_text": day["report_text"],
            "server_time": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        logger.exception("day_report failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weekly-report/{location_id}")
def weekly_report(
    location_id: str,
    week_start: str,
    target_labor_pct: float = 30.0,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Fetch computed weekly P&L report. e.g. ?week_start=2024-01-15"""
    try:
        service = build_service(db)
        week_date = datetime.fromisoformat(week_start).date()
        report = service.get_weekly_report(week_date, location_id, target_labor_pct)
        return {
            "status": "ok",
            "week_start": str(week_date),
            "location_id": location_id,
            "report_dict": {
                k: v for k, v in report["report_dict"].items() if k != "results"
                and k not in ("underperformers", "best_shift", "worst_shift")
            },
            "shift_results": [r.__dict__ for r in report["results"]],
            "report_text": report["report_text"],
        }
    except Exception as e:
        logger.exception("weekly_report failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/shift-history/{shift_id}")
def shift_history(
    shift_id: int,
    location_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Historical performance for a specific shift. e.g. ?location_id=columbus-main&days=30"""
    try:
        service = build_service(db)
        history = service.get_shift_history(shift_id, location_id, days)
        return {
            "status": "ok",
            "shift_id": shift_id,
            "location_id": location_id,
            "days": days,
            "records": history,
        }
    except Exception as e:
        logger.exception("shift_history failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weekly-aggregate/{location_id}")
def weekly_aggregate(
    location_id: str,
    week_start: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Detailed weekly aggregation (by-day breakdown)."""
    try:
        week_date = datetime.fromisoformat(week_start).date()
        agg = WeeklyAggregator(db).aggregate_week(week_date, location_id)
        return {"status": "ok", **agg}
    except Exception as e:
        logger.exception("weekly_aggregate failed")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/initialize-db")
def initialize_database(_: None = Depends(require_api_key)) -> Dict[str, str]:
    """Initialize database tables (dev/admin only)."""
    try:
        init_db()
        return {"status": "ok", "message": "Database tables created."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
