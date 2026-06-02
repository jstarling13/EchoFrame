"""
Real Square connector — live POS revenue + labor punches.

- Revenue:  Square Payments API   (GET  /v2/payments)
- Labor:    Square Labor API      (POST /v2/labor/shifts/search)

Square returns RFC3339 UTC timestamps; we convert them to the configured local
timezone (naive) so they line up with shift-window definitions, exactly like the
mock connector. Set SQUARE_ACCESS_TOKEN to enable; otherwise the connector
reports itself unavailable and the registry raises a clear error.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import List, Dict, Any, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

import httpx

import config
from connectors.base import POSConnector, TimesheetConnector
from logging_config import get_logger

logger = get_logger("connector.square")


def _local_tz():
    if ZoneInfo is not None:
        try:
            return ZoneInfo(config.TIMEZONE)
        except Exception:  # pragma: no cover
            pass
    return timezone.utc


def _day_bounds_utc(day: date) -> tuple[str, str]:
    """Return (begin, end) RFC3339 UTC strings spanning the local business day."""
    tz = _local_tz()
    start_local = datetime.combine(day, time.min).replace(tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        end_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def _to_local_naive(rfc3339: str) -> datetime:
    """Parse an RFC3339 UTC timestamp into a naive datetime in local time."""
    dt = datetime.fromisoformat(rfc3339.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_local_tz()).replace(tzinfo=None)


class _SquareClient:
    """Thin authenticated HTTP wrapper around the Square API."""

    def __init__(self):
        self.base = config.SQUARE_API_BASE.rstrip("/")
        self.token = config.SQUARE_ACCESS_TOKEN
        self.version = config.SQUARE_API_VERSION

    @staticmethod
    def available() -> bool:
        return bool(config.SQUARE_ACCESS_TOKEN)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Square-Version": self.version,
            "Content-Type": "application/json",
        }

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(self.base + path, headers=self._headers(), params=params)
            r.raise_for_status()
            return r.json()

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(self.base + path, headers=self._headers(), json=body)
            r.raise_for_status()
            return r.json()


class SquarePOS(POSConnector):
    name = "square"

    def __init__(self):
        self.client = _SquareClient()

    @staticmethod
    def is_available() -> bool:
        return _SquareClient.available()

    def fetch_transactions(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            raise RuntimeError(
                "Square is not configured. Set SQUARE_ACCESS_TOKEN to use source 'square'."
            )
        begin, end = _day_bounds_utc(day)
        transactions: List[Dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            params = {
                "begin_time": begin,
                "end_time": end,
                "location_id": location_id,
                "sort_order": "ASC",
            }
            if cursor:
                params["cursor"] = cursor
            data = self.client.get("/v2/payments", params)
            for p in data.get("payments", []):
                # Only count completed/approved captured revenue.
                if p.get("status") not in (None, "COMPLETED", "APPROVED", "CAPTURED"):
                    continue
                money = p.get("amount_money") or {}
                cents = money.get("amount")
                if cents is None:
                    continue
                transactions.append({
                    "timestamp": _to_local_naive(p["created_at"]),
                    "amount": round(cents / 100.0, 2),
                    "order_id": p.get("order_id") or p.get("id"),
                    "location_id": location_id,
                    "payment_method": (p.get("source_type") or "card").lower(),
                })
            cursor = data.get("cursor")
            if not cursor:
                break

        logger.info("Square pulled %d payments for %s @ %s", len(transactions), day, location_id)
        return transactions


class SquareTimesheet(TimesheetConnector):
    name = "square"

    def __init__(self):
        self.client = _SquareClient()

    @staticmethod
    def is_available() -> bool:
        return _SquareClient.available()

    def fetch_punches(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            raise RuntimeError(
                "Square is not configured. Set SQUARE_ACCESS_TOKEN to use source 'square'."
            )
        begin, end = _day_bounds_utc(day)
        body = {
            "query": {
                "filter": {
                    "location_ids": [location_id],
                    "start": {"start_at": begin, "end_at": end},
                },
                "sort": {"field": "START_AT", "order": "ASC"},
            },
            "limit": 200,
        }

        punches: List[Dict[str, Any]] = []
        while True:
            data = self.client.post("/v2/labor/shifts/search", body)
            for s in data.get("shifts", []):
                if not s.get("end_at"):
                    continue  # still clocked in; skip until closed
                wage = (s.get("wage") or {}).get("hourly_rate") or {}
                cents = wage.get("amount")
                hourly = round(cents / 100.0, 2) if cents is not None else config.SQUARE_DEFAULT_WAGE
                punches.append({
                    "employee_id": s.get("team_member_id") or s.get("employee_id"),
                    "clock_in": _to_local_naive(s["start_at"]),
                    "clock_out": _to_local_naive(s["end_at"]),
                    "location_id": location_id,
                    "wage": hourly,
                })
            cursor = data.get("cursor")
            if not cursor:
                break
            body["cursor"] = cursor

        logger.info("Square pulled %d shifts for %s @ %s", len(punches), day, location_id)
        return punches
