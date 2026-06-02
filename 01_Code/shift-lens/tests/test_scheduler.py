"""Tests for the auto-sync scheduler's single-pass logic."""

from datetime import date, time

import pytest
from sqlalchemy.orm import sessionmaker

from models.base import Base, make_engine
import models  # noqa: F401
from models.shift_definition import ShiftDefinition
from models.shift_result import ShiftPLResult
import scheduler as scheduler_mod
import config


@pytest.fixture
def patched_session(tmp_path, monkeypatch):
    """Point the scheduler's SessionLocal at an isolated seeded SQLite DB."""
    url = f"sqlite:///{tmp_path / 'sched.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    seed = TestSession()
    # Use today's weekday so the connector's data maps to defined shifts.
    dow = date.today().weekday()
    seed.add_all([
        ShiftDefinition(location_id="loc-1", shift_name="Morning",
                        day_of_week=dow, start_time=time(6, 0), end_time=time(14, 0)),
        ShiftDefinition(location_id="loc-1", shift_name="Afternoon",
                        day_of_week=dow, start_time=time(14, 0), end_time=time(22, 0)),
    ])
    seed.commit()
    seed.close()

    monkeypatch.setattr(scheduler_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(config, "AUTO_SYNC_LOCATIONS", ["loc-1"])
    monkeypatch.setattr(config, "AUTO_SYNC_POS_SOURCE", "mock")
    monkeypatch.setattr(config, "AUTO_SYNC_TIMESHEET_SOURCE", "mock")
    return TestSession


def test_sync_once_populates_results(patched_session):
    summary = scheduler_mod.scheduler.sync_once()
    assert "loc-1" in summary
    assert summary["loc-1"]["total_revenue"] > 0

    db = patched_session()
    try:
        results = db.query(ShiftPLResult).all()
        assert len(results) == 2
    finally:
        db.close()


def test_sync_once_is_idempotent(patched_session):
    scheduler_mod.scheduler.sync_once()
    scheduler_mod.scheduler.sync_once()
    db = patched_session()
    try:
        # Two passes over the same day must not double the result rows.
        assert db.query(ShiftPLResult).count() == 2
    finally:
        db.close()
