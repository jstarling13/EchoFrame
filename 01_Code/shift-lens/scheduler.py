"""
Auto-sync scheduler — keeps "today" current without manual triggers.

A single asyncio background task that, every AUTO_SYNC_INTERVAL_SECONDS, pulls
the current business day from the configured connectors for each configured
location and runs the pipeline. Disabled by default; enable via AUTO_SYNC_ENABLED.

The loop owns its own DB session per tick and swallows/loggs errors so a transient
connector failure never kills the scheduler.
"""

import asyncio
from datetime import date
from typing import Optional

import config
from models.base import SessionLocal
from models.shift_definition import ShiftDefinition
from service.shift_service import ShiftPLService
from connectors import get_pos_connector, get_timesheet_connector
from logging_config import get_logger

logger = get_logger("scheduler")


class AutoSyncScheduler:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    def start(self) -> None:
        if not config.AUTO_SYNC_ENABLED:
            logger.info("auto-sync disabled (set AUTO_SYNC_ENABLED=true to enable)")
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run())
        logger.info(
            "auto-sync started: every %ds for %s via %s/%s",
            config.AUTO_SYNC_INTERVAL_SECONDS, config.AUTO_SYNC_LOCATIONS,
            config.AUTO_SYNC_POS_SOURCE, config.AUTO_SYNC_TIMESHEET_SOURCE,
        )

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._task = None
            logger.info("auto-sync stopped")

    async def _run(self) -> None:
        # Run an immediate tick, then on the configured interval.
        while not self._stop.is_set():
            try:
                await asyncio.to_thread(self.sync_once)
            except Exception:  # noqa: BLE001
                logger.exception("auto-sync tick failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=config.AUTO_SYNC_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass

    def sync_once(self, today: Optional[date] = None) -> dict:
        """One synchronous sync pass across all configured locations."""
        today = today or date.today()
        summary = {}
        db = SessionLocal()
        try:
            pos = get_pos_connector(config.AUTO_SYNC_POS_SOURCE)
            timesheet = get_timesheet_connector(config.AUTO_SYNC_TIMESHEET_SOURCE)
            for location_id in config.AUTO_SYNC_LOCATIONS:
                shifts = (
                    db.query(ShiftDefinition)
                    .filter(ShiftDefinition.location_id == location_id)
                    .all()
                )
                service = ShiftPLService(db, shifts)
                transactions = pos.fetch_transactions(today, location_id)
                punches = timesheet.fetch_punches(today, location_id)
                totals = service.process_day(
                    today, location_id, transactions, punches,
                    target_labor_pct=config.AUTO_SYNC_TARGET_LABOR_PCT,
                )
                summary[location_id] = totals
                logger.info("auto-sync %s @ %s -> %s", today, location_id, totals)
        finally:
            db.close()
        return summary


scheduler = AutoSyncScheduler()
