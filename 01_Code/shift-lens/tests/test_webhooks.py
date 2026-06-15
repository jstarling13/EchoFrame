"""Tests for real-time webhook ingestion + DB-driven recompute."""

from datetime import date, datetime, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from models.base import Base, make_engine
import models  # noqa: F401
from models.shift_definition import ShiftDefinition
from service.shift_service import ShiftPLService
import api_extended
from db import get_db


def _seed_session(tmp_path):
    url = f"sqlite:///{tmp_path / 'wh.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    seed = TestSession()
    seed.add_all([
        ShiftDefinition(location_id="loc-1", shift_name="Mon Morning",
                        day_of_week=0, start_time=time(6, 0), end_time=time(14, 0)),
        ShiftDefinition(location_id="loc-1", shift_name="Mon Afternoon",
                        day_of_week=0, start_time=time(14, 0), end_time=time(22, 0)),
    ])
    seed.commit()
    seed.close()
    return TestSession


class TestRecomputeService:
    def test_recompute_from_db(self, tmp_path):
        TestSession = _seed_session(tmp_path)
        db = TestSession()
        try:
            defs = db.query(ShiftDefinition).all()
            service = ShiftPLService(db, defs)
            shift_date = date(2024, 1, 15)  # Monday

            # Append two raw transactions directly, then recompute from DB.
            from etl.ingestion import ingest_from_dict
            txn_df, _ = ingest_from_dict([
                {"timestamp": datetime(2024, 1, 15, 8, 0), "amount": 100.0,
                 "order_id": "O1", "location_id": "loc-1"},
                {"timestamp": datetime(2024, 1, 15, 9, 0), "amount": 50.0,
                 "order_id": "O2", "location_id": "loc-1"},
            ], [])
            service.persistence.insert_transactions(txn_df)

            totals = service.recompute_day(shift_date, "loc-1")
            assert totals["total_revenue"] == pytest.approx(150.0)
            assert totals["transaction_count"] == 2

            # Recompute again — must stay 150 (no double count).
            totals2 = service.recompute_day(shift_date, "loc-1")
            assert totals2["total_revenue"] == pytest.approx(150.0)
        finally:
            db.close()


class TestWebhookApi:
    @pytest.fixture
    def client(self, tmp_path):
        TestSession = _seed_session(tmp_path)

        def override_get_db():
            db = TestSession()
            try:
                yield db
            finally:
                db.close()

        api_extended.app.dependency_overrides[get_db] = override_get_db
        yield TestClient(api_extended.app)
        api_extended.app.dependency_overrides.clear()

    def test_pos_webhook_updates_day_live(self, client):
        base = {
            "transaction": {
                "timestamp": "2024-01-15T08:30:00", "amount": 200.0,
                "order_id": "W1", "location_id": "loc-1",
            }
        }
        r = client.post("/api/webhooks/pos", json=base)
        assert r.status_code == 200, r.text
        assert r.json()["totals"]["total_revenue"] == pytest.approx(200.0)

        # Second sale pushes revenue up live.
        base["transaction"]["order_id"] = "W2"
        base["transaction"]["amount"] = 75.0
        r2 = client.post("/api/webhooks/pos", json=base)
        assert r2.json()["totals"]["total_revenue"] == pytest.approx(275.0)

    def test_timesheet_webhook(self, client):
        r = client.post("/api/webhooks/timesheet", json={
            "time_punch": {
                "employee_id": "E1", "clock_in": "2024-01-15T06:00:00",
                "clock_out": "2024-01-15T14:00:00", "location_id": "loc-1", "wage": 15.0,
            }
        })
        assert r.status_code == 200, r.text
        assert r.json()["totals"]["total_labor"] == pytest.approx(120.0)

    def test_day_endpoint_reads_live_state(self, client):
        client.post("/api/webhooks/pos", json={
            "transaction": {"timestamp": "2024-01-15T08:30:00", "amount": 200.0,
                            "order_id": "W1", "location_id": "loc-1"}
        })
        r = client.get("/api/day/loc-1", params={"date": "2024-01-15"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["totals"]["total_revenue"] == pytest.approx(200.0)
        assert "server_time" in body

    def test_sources_endpoint(self, client):
        r = client.get("/api/sources")
        assert r.status_code == 200
        body = r.json()
        assert "mock" in body["pos"]
        # Square absent unless a token is configured.
        assert "square" not in body["pos"]
