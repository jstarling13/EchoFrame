"""Mock scheduling/timesheet connector.

Generates a realistic daily roster of clock-in/clock-out punches, including a
mid-shift employee who straddles the morning/afternoon boundary (exercising the
proportional labor-allocation path). Output matches what a real timesheet
provider (e.g. 7shifts, Deputy) would be normalized into.
"""

from datetime import date, datetime, time
from typing import List, Dict, Any

from connectors.base import TimesheetConnector
from logging_config import get_logger

logger = get_logger("connector.timesheet")

# Roster: (employee_id, name, clock_in, clock_out, wage)
_WEEKDAY_ROSTER = [
    ("EMP-001", "Alex Rivera", time(6, 0), time(14, 0), 15.00),
    ("EMP-002", "Bri Chen", time(10, 0), time(18, 0), 16.50),   # straddles boundary
    ("EMP-003", "Cory Diaz", time(14, 0), time(22, 0), 15.50),
]
_WEEKEND_EXTRA = ("EMP-004", "Dana Patel", time(16, 0), time(22, 0), 18.00)


class MockTimesheet(TimesheetConnector):
    name = "mock_timesheet"

    def fetch_punches(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        roster = list(_WEEKDAY_ROSTER)
        if day.weekday() >= 5:
            roster.append(_WEEKEND_EXTRA)

        punches: List[Dict[str, Any]] = []
        for emp_id, name, start, end, wage in roster:
            punches.append({
                "employee_id": emp_id,
                "employee_name": name,
                "clock_in": datetime.combine(day, start),
                "clock_out": datetime.combine(day, end),
                "location_id": location_id,
                "wage": wage,
            })

        logger.info("MockTimesheet pulled %d punches for %s @ %s",
                    len(punches), day, location_id)
        return punches
