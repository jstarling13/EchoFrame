from datetime import date, datetime, time, timedelta
from decimal import Decimal
from collections import defaultdict
from typing import List
import pandas as pd
from sqlalchemy.orm import Session
from models.transaction import POSTransaction
from models.time_punch import TimePunch
from models.shift_mapping import ShiftMapping
from models.shift_result import ShiftPLResult
from models.shift_definition import ShiftDefinition
from logging_config import get_logger

logger = get_logger("persistence")

class ShiftDataPersistence:
    """Handles database persistence for shift mapping and P&L results."""

    def __init__(self, session: Session):
        self.session = session

    def clear_day(self, shift_date: date, location_id: str) -> dict:
        """
        Remove all data for a (date, location) so the day can be reprocessed
        idempotently. Deletes computed results, mappings, and the raw rows whose
        timestamps fall on that calendar day.

        Returns a count of rows deleted per table.
        """
        day_start = datetime.combine(shift_date, time.min)
        day_end = day_start + timedelta(days=1)

        results_deleted = (
            self.session.query(ShiftPLResult)
            .filter(
                ShiftPLResult.date == shift_date,
                ShiftPLResult.shift_definition_id.in_(
                    self.session.query(ShiftDefinition.id).filter(
                        ShiftDefinition.location_id == location_id
                    )
                ),
            )
            .delete(synchronize_session=False)
        )

        mappings_deleted = (
            self.session.query(ShiftMapping)
            .filter(
                ShiftMapping.date == shift_date,
                ShiftMapping.shift_definition_id.in_(
                    self.session.query(ShiftDefinition.id).filter(
                        ShiftDefinition.location_id == location_id
                    )
                ),
            )
            .delete(synchronize_session=False)
        )

        txns_deleted = (
            self.session.query(POSTransaction)
            .filter(
                POSTransaction.location_id == location_id,
                POSTransaction.timestamp >= day_start,
                POSTransaction.timestamp < day_end,
            )
            .delete(synchronize_session=False)
        )

        punches_deleted = (
            self.session.query(TimePunch)
            .filter(
                TimePunch.location_id == location_id,
                TimePunch.clock_in >= day_start,
                TimePunch.clock_in < day_end,
            )
            .delete(synchronize_session=False)
        )

        self.session.commit()
        deleted = {
            "results": results_deleted,
            "mappings": mappings_deleted,
            "transactions": txns_deleted,
            "punches": punches_deleted,
        }
        logger.info("clear_day %s @ %s removed %s", shift_date, location_id, deleted)
        return deleted

    def insert_transactions(self, transactions_df: pd.DataFrame) -> List[POSTransaction]:
        """Bulk insert transactions."""
        if transactions_df.empty:
            return []

        objs = [
            POSTransaction(
                timestamp=row["timestamp"],
                amount=Decimal(str(row["amount"])),
                order_id=str(row["order_id"]),
                location_id=str(row["location_id"]),
            )
            for _, row in transactions_df.iterrows()
        ]
        self.session.add_all(objs)
        self.session.commit()
        logger.info("inserted %d transactions", len(objs))
        return objs

    def insert_punches(self, punches_df: pd.DataFrame) -> List[TimePunch]:
        """Bulk insert time punches."""
        if punches_df.empty:
            return []

        objs = [
            TimePunch(
                employee_id=str(row["employee_id"]),
                clock_in=row["clock_in"],
                clock_out=row.get("clock_out"),
                location_id=str(row["location_id"]),
                wage_override=Decimal(str(row["wage"])) if pd.notna(row.get("wage")) else None,
            )
            for _, row in punches_df.iterrows()
        ]
        self.session.add_all(objs)
        self.session.commit()
        logger.info("inserted %d time punches", len(objs))
        return objs

    def insert_shift_mappings(self, mappings_df: pd.DataFrame, shift_date: date) -> List[ShiftMapping]:
        """Persist shift mapping records."""
        if mappings_df.empty:
            return []

        objs = [
            ShiftMapping(
                shift_definition_id=row["shift_definition_id"],
                transaction_id=row.get("transaction_id"),
                time_punch_id=row.get("time_punch_id"),
                revenue_allocation=Decimal(str(row.get("revenue_allocation", 0))),
                labor_allocation=Decimal(str(row.get("labor_allocation", 0))),
                date=shift_date,
            )
            for _, row in mappings_df.iterrows()
            if row.get("shift_definition_id") is not None
        ]
        self.session.add_all(objs)
        self.session.commit()
        return objs

    def compute_and_store_pl_results(
        self,
        shift_date: date,
        location_id: str,
        target_labor_pct: float = 30.0
    ) -> List[ShiftPLResult]:
        """
        Query shift mappings for the date, aggregate by shift, and store P&L results.
        """
        mappings = (
            self.session.query(ShiftMapping)
            .join(ShiftDefinition)
            .filter(
                ShiftMapping.date == shift_date,
                ShiftDefinition.location_id == location_id,
            )
            .all()
        )

        grouped = defaultdict(lambda: {"revenue": Decimal(0), "labor": Decimal(0)})
        for m in mappings:
            shift_id = m.shift_definition_id
            grouped[shift_id]["revenue"] += m.revenue_allocation or Decimal(0)
            grouped[shift_id]["labor"] += m.labor_allocation or Decimal(0)

        results = []
        for shift_id, totals in grouped.items():
            revenue = totals["revenue"]
            labor = totals["labor"]
            labor_pct = float(labor / revenue * 100) if revenue > 0 else None
            contribution = revenue - labor
            status = self._classify_shift(revenue, labor, labor_pct, target_labor_pct)

            result = ShiftPLResult(
                shift_definition_id=shift_id,
                date=shift_date,
                total_revenue=revenue,
                total_labor_cost=labor,
                labor_pct=labor_pct,
                contribution=contribution,
                status=status,
            )
            results.append(result)

        self.session.add_all(results)
        self.session.commit()
        logger.info(
            "computed %d shift P&L result(s) for %s @ %s",
            len(results), shift_date, location_id,
        )
        return results

    def _classify_shift(
        self,
        revenue: Decimal,
        labor_cost: Decimal,
        labor_pct: float,
        target_labor_pct: float
    ) -> str:
        """Classify shift status based on P&L metrics."""
        if revenue <= 0:
            return "no_revenue"
        if labor_cost >= revenue:
            return "underperforming"
        if labor_pct is not None and labor_pct > target_labor_pct * 1.5:
            return "underperforming"
        if labor_pct is not None and labor_pct > target_labor_pct:
            return "watch"
        return "healthy"
