"""Abstract connector interfaces for POS and timesheet integrations."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any


class POSConnector(ABC):
    """Pulls raw POS transactions for a (date, location)."""

    name: str = "abstract-pos"

    @abstractmethod
    def fetch_transactions(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        """
        Return a list of transaction dicts:
            {timestamp: datetime, amount: float, order_id: str, location_id: str}
        """
        raise NotImplementedError


class TimesheetConnector(ABC):
    """Pulls raw employee time punches for a (date, location)."""

    name: str = "abstract-timesheet"

    @abstractmethod
    def fetch_punches(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        """
        Return a list of punch dicts:
            {employee_id: str, clock_in: datetime, clock_out: datetime,
             location_id: str, wage: float}
        """
        raise NotImplementedError
