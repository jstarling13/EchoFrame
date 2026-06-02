from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from decimal import Decimal
from sqlalchemy.orm import Session

from models.shift_definition import ShiftDefinition
from models.shift_result import ShiftPLResult
from etl.shift_mapper import ShiftMapper
from etl.labor_allocator import LaborAllocator
from etl.persistence import ShiftDataPersistence
from etl.ingestion import ingest_from_dict
from logging_config import get_logger
import engine

logger = get_logger("service")

class ShiftPLService:
    """Orchestrates ETL pipeline: ingest → map → allocate → persist → analyze."""

    def __init__(self, db_session: Session, shift_definitions: List[ShiftDefinition]):
        self.session = db_session
        self.shift_definitions = shift_definitions
        self.mapper = ShiftMapper(shift_definitions)
        self.allocator = LaborAllocator(shift_definitions)
        self.persistence = ShiftDataPersistence(db_session)

    def process_day(
        self,
        shift_date: date,
        location_id: str,
        raw_transactions: List[Dict[str, Any]],
        raw_punches: List[Dict[str, Any]],
        target_labor_pct: float = 30.0,
        reprocess: bool = True,
    ) -> Dict[str, Any]:
        """
        Full ETL pipeline for a single day.

        Args:
            shift_date: Date to process
            location_id: Location identifier
            raw_transactions: List of transaction dicts
            raw_punches: List of time punch dicts
            target_labor_pct: Target labor cost percentage
            reprocess: If True (default), clear any existing data for this
                (date, location) first so re-running is idempotent — no double counting.

        Returns:
            Summary dict with shift counts and totals
        """
        logger.info(
            "process_day start %s @ %s (%d txns, %d punches, reprocess=%s)",
            shift_date, location_id, len(raw_transactions), len(raw_punches), reprocess,
        )

        if reprocess:
            self.persistence.clear_day(shift_date, location_id)

        txn_df, punch_df = ingest_from_dict(raw_transactions, raw_punches)

        txn_mapped = self.mapper.map_transactions_to_shifts(txn_df, shift_date, location_id)
        labor_mapped = self.allocator.allocate_labor_across_shifts(punch_df, shift_date, location_id)

        merged = self._merge_revenue_and_labor(txn_mapped, labor_mapped)

        self.persistence.insert_transactions(txn_df)
        self.persistence.insert_punches(punch_df)
        self.persistence.insert_shift_mappings(merged, shift_date)
        self.persistence.compute_and_store_pl_results(shift_date, location_id, target_labor_pct)

        totals = {
            "total_revenue": float(merged["revenue_allocation"].sum() if not merged.empty else 0),
            "total_labor": float(merged["labor_allocation"].sum() if not merged.empty else 0),
            "transaction_count": len(txn_df),
            "punch_count": len(punch_df),
        }

        logger.info("process_day done %s @ %s totals=%s", shift_date, location_id, totals)
        return totals

    def recompute_day(
        self,
        shift_date: date,
        location_id: str,
        target_labor_pct: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Re-map and re-cost a day using the raw transactions/punches already stored
        in the database (no re-ingestion). This is what webhook events and the
        auto-sync scheduler call after appending new raw rows. Idempotent: it
        clears only the derived mappings/results, never the raw data.
        """
        txn_df, punch_df = self.persistence.get_raw_for_day(shift_date, location_id)

        txn_mapped = self.mapper.map_transactions_to_shifts(txn_df, shift_date, location_id)
        labor_mapped = self.allocator.allocate_labor_across_shifts(punch_df, shift_date, location_id)
        merged = self._merge_revenue_and_labor(txn_mapped, labor_mapped)

        self.persistence.clear_derived_for_day(shift_date, location_id)
        self.persistence.insert_shift_mappings(merged, shift_date)
        self.persistence.compute_and_store_pl_results(shift_date, location_id, target_labor_pct)

        totals = {
            "total_revenue": float(merged["revenue_allocation"].sum() if not merged.empty else 0),
            "total_labor": float(merged["labor_allocation"].sum() if not merged.empty else 0),
            "transaction_count": int(len(txn_df)),
            "punch_count": int(len(punch_df)),
        }
        logger.info("recompute_day %s @ %s totals=%s", shift_date, location_id, totals)
        return totals

    def get_day_report(
        self,
        shift_date: date,
        location_id: str,
        target_labor_pct: float = 30.0,
    ) -> Dict[str, Any]:
        """Read a single day's stored P&L results and render a report."""
        from models.shift_result import ShiftPLResult  # local import to avoid cycle noise

        results = (
            self.session.query(ShiftPLResult)
            .join(ShiftDefinition)
            .filter(ShiftPLResult.date == shift_date,
                    ShiftDefinition.location_id == location_id)
            .all()
        )
        shifts = [
            engine.Shift(label=r.shift_definition.shift_name,
                         revenue=float(r.total_revenue),
                         labor_cost=float(r.total_labor_cost))
            for r in results
        ]
        report_dict = engine.analyze_week(shifts, target_labor_pct=target_labor_pct)
        return {
            "date": str(shift_date),
            "results": report_dict["results"],
            "report_dict": report_dict,
            "report_text": engine.render_report_text(report_dict),
        }

    def _merge_revenue_and_labor(
        self,
        txn_mapped: pd.DataFrame,
        labor_mapped: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge transaction and labor mappings into a unified mapping."""
        if txn_mapped.empty and labor_mapped.empty:
            return pd.DataFrame(
                columns=["shift_definition_id", "revenue_allocation", "labor_allocation"]
            )

        # Keep allocations as floats here so pandas can aggregate them; persistence
        # converts to Decimal at the DB boundary. (Mixing float + Decimal breaks sum.)
        mappings = []

        if not txn_mapped.empty:
            for _, row in txn_mapped.iterrows():
                mappings.append({
                    "shift_definition_id": row["shift_definition_id"],
                    "revenue_allocation": float(row["amount"]) if row["allocation_pct"] > 0 else 0.0,
                    "labor_allocation": 0.0,
                })

        if not labor_mapped.empty:
            for _, row in labor_mapped.iterrows():
                mappings.append({
                    "shift_definition_id": row["shift_definition_id"],
                    "revenue_allocation": 0.0,
                    "labor_allocation": float(row["labor_cost"]),
                })

        merged = pd.DataFrame(mappings)
        if not merged.empty:
            merged = merged.groupby("shift_definition_id").agg({
                "revenue_allocation": "sum",
                "labor_allocation": "sum",
            }).reset_index()

        return merged

    def get_weekly_report(
        self,
        week_start: date,
        location_id: str,
        target_labor_pct: float = 30.0
    ) -> Dict[str, Any]:
        """
        Generate a weekly P&L report from stored results.

        Returns a dict compatible with the MVP's engine.render_report_text()
        """
        end_date = week_start + timedelta(days=7)

        results = (
            self.session.query(ShiftPLResult)
            .join(ShiftDefinition)
            .filter(
                ShiftPLResult.date >= week_start,
                ShiftPLResult.date < end_date,
                ShiftDefinition.location_id == location_id,
            )
            .all()
        )

        # Rebuild raw Shift inputs from the stored P&L and let the MVP engine
        # produce the canonical report (status, recommendations, ranking, totals).
        shifts = [
            engine.Shift(
                label=r.shift_definition.shift_name,
                revenue=float(r.total_revenue),
                labor_cost=float(r.total_labor_cost),
            )
            for r in results
        ]

        report_dict = engine.analyze_week(shifts, target_labor_pct=target_labor_pct)
        return {
            "results": report_dict["results"],
            "report_dict": report_dict,
            "report_text": engine.render_report_text(report_dict),
        }

    def _get_recommendation(self, pl_result: ShiftPLResult) -> str:
        """Generate a recommendation based on shift status."""
        if pl_result.status == "no_revenue":
            return "No revenue recorded. Consider cutting or merging this shift."
        elif pl_result.status == "underperforming":
            if pl_result.total_labor_cost >= pl_result.total_revenue:
                return "Labor meets/exceeds revenue. Cut shift, shorten it, or reduce headcount."
            else:
                return f"Labor is {pl_result.labor_pct:.0f}% of revenue, well above target. Reduce headcount."
        elif pl_result.status == "watch":
            return f"Labor is {pl_result.labor_pct:.0f}% of revenue, above target. Trim one position or tighten schedule."
        else:
            return f"Labor is {pl_result.labor_pct:.0f}% of revenue — on target. Keep this schedule."

    def get_shift_history(
        self,
        shift_definition_id: int,
        location_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance for a specific shift.

        Returns: List of daily records with revenue, labor, and status
        """
        cutoff_date = date.today() - timedelta(days=days)

        results = (
            self.session.query(ShiftPLResult)
            .join(ShiftDefinition)
            .filter(
                ShiftPLResult.shift_definition_id == shift_definition_id,
                ShiftPLResult.date >= cutoff_date,
                ShiftDefinition.location_id == location_id,
            )
            .order_by(ShiftPLResult.date)
            .all()
        )

        return [
            {
                "date": str(r.date),
                "revenue": float(r.total_revenue),
                "labor": float(r.total_labor_cost),
                "labor_pct": float(r.labor_pct) if r.labor_pct is not None else None,
                "contribution": float(r.contribution),
                "status": r.status,
            }
            for r in results
        ]
