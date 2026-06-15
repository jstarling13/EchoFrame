from datetime import datetime, date, time, timedelta
from typing import List
from decimal import Decimal
import pandas as pd
from models.shift_definition import ShiftDefinition

class LaborAllocator:
    """Allocates labor costs across shift blocks (handles split shifts)."""

    def __init__(self, shift_definitions: List[ShiftDefinition]):
        self.shifts = shift_definitions

    def allocate_labor_across_shifts(
        self,
        time_punches: pd.DataFrame,
        shift_date: date,
        location_id: str
    ) -> pd.DataFrame:
        """
        Allocate labor costs proportionally across shifts.

        Each time punch may span multiple shifts; labor cost is split proportionally.

        Args:
            time_punches: DataFrame with columns [employee_id, clock_in, clock_out, wage]
            shift_date: Date for which to allocate
            location_id: Location identifier

        Returns:
            DataFrame with columns [time_punch_id, shift_definition_id, hours, labor_cost, employee_id]
        """
        shifts_for_date = [
            s for s in self.shifts
            if s.location_id == location_id and s.day_of_week == shift_date.weekday()
        ]

        if not shifts_for_date:
            return pd.DataFrame(columns=["time_punch_id", "shift_definition_id", "hours", "labor_cost", "employee_id"])

        results = []
        for idx, row in time_punches.iterrows():
            clock_in = row["clock_in"]
            clock_out = row["clock_out"] if pd.notna(row.get("clock_out")) else datetime.now()
            wage = Decimal(str(row["wage"]))
            punch_id = row.get("id", idx)
            employee_id = row["employee_id"]

            total_hours = (clock_out - clock_in).total_seconds() / 3600.0

            for shift in shifts_for_date:
                overlap_hours = self._calc_overlap_hours(clock_in, clock_out, shift.start_time, shift.end_time, shift_date)

                if overlap_hours > 0:
                    labor_cost = Decimal(str(overlap_hours)) * wage
                    results.append({
                        "time_punch_id": punch_id,
                        "shift_definition_id": shift.id,
                        "hours": round(overlap_hours, 2),
                        "labor_cost": float(labor_cost),
                        "employee_id": employee_id,
                    })

        return pd.DataFrame(results)

    def _calc_overlap_hours(
        self,
        clock_in: datetime,
        clock_out: datetime,
        shift_start: time,
        shift_end: time,
        shift_date: date
    ) -> float:
        """Calculate hours of overlap between punch and shift block."""
        shift_start_dt = datetime.combine(shift_date, shift_start)
        shift_end_dt = datetime.combine(shift_date, shift_end)

        if shift_end <= shift_start:
            shift_end_dt += timedelta(days=1)

        overlap_start = max(clock_in, shift_start_dt)
        overlap_end = min(clock_out, shift_end_dt)

        if overlap_end <= overlap_start:
            return 0.0

        return (overlap_end - overlap_start).total_seconds() / 3600.0
