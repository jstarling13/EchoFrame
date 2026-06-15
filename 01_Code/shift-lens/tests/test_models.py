"""DB-backed tests for ORM models and persistence."""

from datetime import datetime, date, time
from decimal import Decimal

from models.employee import Employee
from models.transaction import POSTransaction
from models.time_punch import TimePunch
from models.shift_definition import ShiftDefinition
from models.shift_mapping import ShiftMapping
from models.shift_result import ShiftPLResult


class TestModels:
    def test_create_employee(self, db_session):
        emp = Employee(id="EMP-001", name="Alex", base_wage=Decimal("15.00"), location_id="loc-1")
        db_session.add(emp)
        db_session.commit()

        fetched = db_session.query(Employee).filter_by(id="EMP-001").one()
        assert fetched.name == "Alex"
        assert fetched.base_wage == Decimal("15.00")

    def test_transaction_persists(self, db_session):
        txn = POSTransaction(
            timestamp=datetime(2024, 1, 15, 8, 30),
            amount=Decimal("45.50"),
            order_id="ORD-1",
            location_id="loc-1",
        )
        db_session.add(txn)
        db_session.commit()

        fetched = db_session.query(POSTransaction).one()
        assert fetched.amount == Decimal("45.50")
        assert fetched.order_id == "ORD-1"

    def test_employee_punch_relationship(self, db_session):
        emp = Employee(id="EMP-002", name="Bri", base_wage=Decimal("16.00"), location_id="loc-1")
        punch = TimePunch(
            employee_id="EMP-002",
            clock_in=datetime(2024, 1, 15, 6, 0),
            clock_out=datetime(2024, 1, 15, 14, 0),
            location_id="loc-1",
        )
        db_session.add_all([emp, punch])
        db_session.commit()

        fetched_emp = db_session.query(Employee).filter_by(id="EMP-002").one()
        assert len(fetched_emp.time_punches) == 1
        assert fetched_emp.time_punches[0].clock_in == datetime(2024, 1, 15, 6, 0)

    def test_shift_definition_and_result_relationship(self, db_session):
        sd = ShiftDefinition(
            location_id="loc-1", shift_name="Mon Morning",
            day_of_week=0, start_time=time(6, 0), end_time=time(14, 0),
        )
        db_session.add(sd)
        db_session.commit()

        result = ShiftPLResult(
            shift_definition_id=sd.id, date=date(2024, 1, 15),
            total_revenue=Decimal("1000"), total_labor_cost=Decimal("300"),
            labor_pct=Decimal("30.0"), contribution=Decimal("700"), status="healthy",
        )
        db_session.add(result)
        db_session.commit()

        fetched = db_session.query(ShiftDefinition).filter_by(id=sd.id).one()
        assert len(fetched.shift_pl_results) == 1
        assert fetched.shift_pl_results[0].status == "healthy"

    def test_shift_mapping_persists(self, db_session):
        sd = ShiftDefinition(
            location_id="loc-1", shift_name="Mon Morning",
            day_of_week=0, start_time=time(6, 0), end_time=time(14, 0),
        )
        db_session.add(sd)
        db_session.commit()

        mapping = ShiftMapping(
            shift_definition_id=sd.id, date=date(2024, 1, 15),
            revenue_allocation=Decimal("125.50"), labor_allocation=Decimal("60.00"),
        )
        db_session.add(mapping)
        db_session.commit()

        fetched = db_session.query(ShiftMapping).one()
        assert fetched.revenue_allocation == Decimal("125.50")
        assert fetched.shift_definition.shift_name == "Mon Morning"
