"""End-to-end DB-backed tests for the ShiftPLService pipeline."""

from datetime import datetime, date, time
from decimal import Decimal

import pytest

from models.shift_definition import ShiftDefinition
from models.shift_result import ShiftPLResult
from models.transaction import POSTransaction
from service.shift_service import ShiftPLService


def make_shift_defs(session):
    defs = [
        ShiftDefinition(location_id="loc-1", shift_name="Mon Morning",
                        day_of_week=0, start_time=time(6, 0), end_time=time(14, 0)),
        ShiftDefinition(location_id="loc-1", shift_name="Mon Afternoon",
                        day_of_week=0, start_time=time(14, 0), end_time=time(22, 0)),
    ]
    session.add_all(defs)
    session.commit()
    return defs


SHIFT_DATE = date(2024, 1, 15)  # a Monday


def sample_inputs():
    transactions = [
        {"timestamp": datetime(2024, 1, 15, 8, 0), "amount": 100.0, "order_id": "O1", "location_id": "loc-1"},
        {"timestamp": datetime(2024, 1, 15, 12, 0), "amount": 200.0, "order_id": "O2", "location_id": "loc-1"},
        {"timestamp": datetime(2024, 1, 15, 16, 0), "amount": 500.0, "order_id": "O3", "location_id": "loc-1"},
    ]
    punches = [
        {"employee_id": "E1", "clock_in": datetime(2024, 1, 15, 6, 0),
         "clock_out": datetime(2024, 1, 15, 14, 0), "location_id": "loc-1", "wage": 15.0},
        {"employee_id": "E2", "clock_in": datetime(2024, 1, 15, 14, 0),
         "clock_out": datetime(2024, 1, 15, 22, 0), "location_id": "loc-1", "wage": 16.0},
    ]
    return transactions, punches


class TestServicePipeline:
    def test_process_day_persists_results(self, db_session):
        defs = make_shift_defs(db_session)
        service = ShiftPLService(db_session, defs)
        txns, punches = sample_inputs()

        totals = service.process_day(SHIFT_DATE, "loc-1", txns, punches)

        # Revenue: 100+200 morning, 500 afternoon = 800 total.
        assert totals["total_revenue"] == pytest.approx(800.0)
        # Labor: E1 8h*15=120 morning, E2 8h*16=128 afternoon = 248.
        assert totals["total_labor"] == pytest.approx(248.0)

        results = db_session.query(ShiftPLResult).all()
        assert len(results) == 2

        morning = next(r for r in results if r.shift_definition.shift_name == "Mon Morning")
        assert float(morning.total_revenue) == pytest.approx(300.0)
        assert float(morning.total_labor_cost) == pytest.approx(120.0)
        assert morning.status == "watch"  # 40% labor > 30% target, < 45%

    def test_reprocessing_is_idempotent(self, db_session):
        defs = make_shift_defs(db_session)
        service = ShiftPLService(db_session, defs)
        txns, punches = sample_inputs()

        service.process_day(SHIFT_DATE, "loc-1", txns, punches)
        first_txn_count = db_session.query(POSTransaction).count()
        first_result_count = db_session.query(ShiftPLResult).count()

        # Run again with identical data — must NOT double-count.
        service.process_day(SHIFT_DATE, "loc-1", txns, punches)
        assert db_session.query(POSTransaction).count() == first_txn_count
        assert db_session.query(ShiftPLResult).count() == first_result_count

    def test_weekly_report_from_db(self, db_session):
        defs = make_shift_defs(db_session)
        service = ShiftPLService(db_session, defs)
        txns, punches = sample_inputs()
        service.process_day(SHIFT_DATE, "loc-1", txns, punches)

        report = service.get_weekly_report(SHIFT_DATE, "loc-1")
        assert len(report["results"]) == 2
        assert "SHIFT LENS" in report["report_text"]

    def test_shift_history(self, db_session):
        defs = make_shift_defs(db_session)
        service = ShiftPLService(db_session, defs)
        txns, punches = sample_inputs()
        # Use today so the 30-day history window includes it.
        from datetime import date as _date
        today = _date.today()
        # Shift inputs onto a matching weekday is unnecessary; mapping uses today's weekday.
        for t in txns:
            t["timestamp"] = datetime.combine(today, t["timestamp"].time())
        for p in punches:
            p["clock_in"] = datetime.combine(today, p["clock_in"].time())
            p["clock_out"] = datetime.combine(today, p["clock_out"].time())

        # Rebuild defs for today's weekday so mapping finds shifts.
        for d in defs:
            d.day_of_week = today.weekday()
        db_session.commit()

        service.process_day(today, "loc-1", txns, punches)
        history = service.get_shift_history(defs[0].id, "loc-1", days=30)
        assert len(history) >= 1
        assert history[0]["status"] in {"healthy", "watch", "underperforming", "no_revenue"}
