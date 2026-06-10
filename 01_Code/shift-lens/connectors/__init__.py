"""
Connector layer — pluggable integrations with POS and timesheet systems.

The mock connectors simulate pulling a day of data from external systems
(Square/Toast-style POS, a scheduling/timesheet provider). Swapping in a real
integration means implementing the same `POSConnector` / `TimesheetConnector`
interface — the ETL/service layers don't change.
"""

from connectors.base import POSConnector, TimesheetConnector
from connectors.mock_pos import MockSquarePOS
from connectors.mock_timesheet import MockTimesheet
from connectors.square import SquarePOS, SquareTimesheet

_POS_REGISTRY = {
    "mock": MockSquarePOS,
    "mock_square": MockSquarePOS,
    "square": SquarePOS,
}
_TIMESHEET_REGISTRY = {
    "mock": MockTimesheet,
    "mock_timesheet": MockTimesheet,
    "square": SquareTimesheet,
}


def available_sources() -> dict:
    """Report which sources are usable right now (Square needs a token)."""
    return {
        "pos": [name for name in _POS_REGISTRY
                if name != "square" or SquarePOS.is_available()],
        "timesheet": [name for name in _TIMESHEET_REGISTRY
                      if name != "square" or SquareTimesheet.is_available()],
    }


def get_pos_connector(name: str = "mock") -> POSConnector:
    """Return a POS connector by name (defaults to the mock)."""
    try:
        connector = _POS_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown POS connector '{name}'. Available: {sorted(_POS_REGISTRY)}"
        )
    if name == "square" and not SquarePOS.is_available():
        raise ValueError("Square POS is not configured. Set SQUARE_ACCESS_TOKEN.")
    return connector


def get_timesheet_connector(name: str = "mock") -> TimesheetConnector:
    """Return a timesheet connector by name (defaults to the mock)."""
    try:
        connector = _TIMESHEET_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown timesheet connector '{name}'. Available: {sorted(_TIMESHEET_REGISTRY)}"
        )
    if name == "square" and not SquareTimesheet.is_available():
        raise ValueError("Square timesheet is not configured. Set SQUARE_ACCESS_TOKEN.")
    return connector


__all__ = [
    "POSConnector",
    "TimesheetConnector",
    "MockSquarePOS",
    "MockTimesheet",
    "SquarePOS",
    "SquareTimesheet",
    "get_pos_connector",
    "get_timesheet_connector",
    "available_sources",
]
