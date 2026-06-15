from datetime import date, timedelta
from typing import List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.shift_result import ShiftPLResult
from models.shift_definition import ShiftDefinition

class WeeklyAggregator:
    """Aggregates shift results into weekly summaries."""

    def __init__(self, session: Session):
        self.session = session

    def aggregate_week(
        self,
        week_start: date,
        location_id: str
    ) -> Dict[str, Any]:
        """
        Aggregate all shifts for a week.

        Returns:
            Dict with totals and day-by-day breakdown
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

        total_revenue = sum(r.total_revenue for r in results)
        total_labor = sum(r.total_labor_cost for r in results)
        overall_labor_pct = (total_labor / total_revenue * 100) if total_revenue > 0 else None

        by_day = {}
        for r in results:
            day_key = str(r.date)
            if day_key not in by_day:
                by_day[day_key] = {"revenue": Decimal(0), "labor": Decimal(0), "shifts": []}
            by_day[day_key]["revenue"] += r.total_revenue
            by_day[day_key]["labor"] += r.total_labor_cost
            by_day[day_key]["shifts"].append(r.shift_definition.shift_name)

        return {
            "week_start": str(week_start),
            "total_revenue": float(total_revenue),
            "total_labor": float(total_labor),
            "overall_labor_pct": float(overall_labor_pct) if overall_labor_pct else None,
            "total_contribution": float(total_revenue - total_labor),
            "by_day": {
                day: {
                    "revenue": float(data["revenue"]),
                    "labor": float(data["labor"]),
                    "shifts": data["shifts"],
                }
                for day, data in by_day.items()
            },
        }

class ShiftHistoryAnalyzer:
    """Analyzes historical patterns for specific shifts."""

    def __init__(self, session: Session):
        self.session = session

    def analyze_shift_pattern(
        self,
        shift_definition_id: int,
        location_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze performance pattern for a shift over time.

        Returns:
            Dict with trend data, averages, and volatility metrics
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

        if not results:
            return {}

        revenues = [float(r.total_revenue) for r in results]
        labors = [float(r.total_labor_cost) for r in results]
        labor_pcts = [float(r.labor_pct) if r.labor_pct else None for r in results]
        labor_pcts = [x for x in labor_pcts if x is not None]

        avg_revenue = sum(revenues) / len(revenues) if revenues else 0
        avg_labor = sum(labors) / len(labors) if labors else 0
        avg_labor_pct = sum(labor_pcts) / len(labor_pcts) if labor_pcts else 0

        return {
            "shift_id": shift_definition_id,
            "period_days": days,
            "samples": len(results),
            "avg_revenue": round(avg_revenue, 2),
            "avg_labor": round(avg_labor, 2),
            "avg_labor_pct": round(avg_labor_pct, 1),
            "min_revenue": round(min(revenues), 2) if revenues else 0,
            "max_revenue": round(max(revenues), 2) if revenues else 0,
            "healthy_count": sum(1 for r in results if r.status == "healthy"),
            "watch_count": sum(1 for r in results if r.status == "watch"),
            "underperforming_count": sum(1 for r in results if r.status == "underperforming"),
        }
