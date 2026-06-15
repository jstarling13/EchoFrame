"""Integration tests for the extended API (connector sync, reporting, auth)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from models.base import Base, make_engine
import models  # noqa: F401
from models.shift_definition import ShiftDefinition
import api_extended
from db import get_db


@pytest.fixture
def client(tmp_path):
    """TestClient with an isolated SQLite DB and seeded shift definitions."""
    url = f"sqlite:///{tmp_path / 'api.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    # Seed shift definitions for all 7 days so any date maps.
    seed = TestSession()
    from datetime import time
    for dow in range(7):
        seed.add_all([
            ShiftDefinition(location_id="loc-1", shift_name=f"D{dow} Morning",
                            day_of_week=dow, start_time=time(6, 0), end_time=time(14, 0)),
            ShiftDefinition(location_id="loc-1", shift_name=f"D{dow} Afternoon",
                            day_of_week=dow, start_time=time(14, 0), end_time=time(22, 0)),
        ])
    seed.commit()
    seed.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    api_extended.app.dependency_overrides[get_db] = override_get_db
    client = TestClient(api_extended.app)
    yield client
    api_extended.app.dependency_overrides.clear()


class TestApi:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_shifts(self, client):
        r = client.get("/api/shifts/loc-1")
        assert r.status_code == 200
        assert len(r.json()["shifts"]) == 14

    def test_sync_day_runs_pipeline(self, client):
        target = date(2024, 1, 15).isoformat()
        r = client.post("/api/sync-day", json={
            "date": target, "location_id": "loc-1",
            "pos_source": "mock", "timesheet_source": "mock",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["totals"]["total_revenue"] > 0
        assert body["totals"]["total_labor"] > 0
        assert len(body["shift_results"]) == 2
        assert "SHIFT LENS" in body["report_text"]

    def test_sync_then_weekly_report(self, client):
        target = date(2024, 1, 15)
        client.post("/api/sync-day", json={
            "date": target.isoformat(), "location_id": "loc-1",
        })
        # week_start = Monday of that week
        week_start = (target - timedelta(days=target.weekday())).isoformat()
        r = client.get(f"/api/weekly-report/loc-1", params={"week_start": week_start})
        assert r.status_code == 200, r.text
        assert len(r.json()["shift_results"]) >= 1

    def test_sync_unknown_source_400(self, client):
        r = client.post("/api/sync-day", json={
            "date": date(2024, 1, 15).isoformat(), "location_id": "loc-1",
            "pos_source": "does-not-exist",
        })
        assert r.status_code == 400

    def test_process_day_validation_error(self, client):
        # Missing required fields -> 422 from pydantic
        r = client.post("/api/process-day", json={"date": "2024-01-15"})
        assert r.status_code == 422


class TestAuth:
    def test_auth_enforced_when_key_set(self, client, monkeypatch):
        monkeypatch.setattr(api_extended.config, "API_KEY", "secret123")
        # No header -> 401
        r = client.post("/api/sync-day", json={
            "date": date(2024, 1, 15).isoformat(), "location_id": "loc-1",
        })
        assert r.status_code == 401
        # Correct header -> 200
        r2 = client.post("/api/sync-day",
                         headers={"X-API-Key": "secret123"},
                         json={"date": date(2024, 1, 15).isoformat(), "location_id": "loc-1"})
        assert r2.status_code == 200

    def test_read_endpoints_open(self, client, monkeypatch):
        monkeypatch.setattr(api_extended.config, "API_KEY", "secret123")
        # GET endpoints remain accessible without a key.
        assert client.get("/api/shifts/loc-1").status_code == 200
