"""Tests for the mock POS and timesheet connectors."""

from datetime import date

import pytest

from connectors import (
    get_pos_connector,
    get_timesheet_connector,
    MockSquarePOS,
    MockTimesheet,
)

WEEKDAY = date(2024, 1, 15)   # Monday
WEEKEND = date(2024, 1, 20)   # Saturday


class TestPOSConnector:
    def test_returns_transactions(self):
        pos = MockSquarePOS()
        txns = pos.fetch_transactions(WEEKDAY, "loc-1")
        assert len(txns) > 0
        for t in txns:
            assert set(t) >= {"timestamp", "amount", "order_id", "location_id"}
            assert t["location_id"] == "loc-1"
            assert t["amount"] > 0

    def test_deterministic(self):
        pos = MockSquarePOS()
        a = pos.fetch_transactions(WEEKDAY, "loc-1")
        b = pos.fetch_transactions(WEEKDAY, "loc-1")
        assert [t["order_id"] for t in a] == [t["order_id"] for t in b]
        assert [t["amount"] for t in a] == [t["amount"] for t in b]

    def test_chronological(self):
        txns = MockSquarePOS().fetch_transactions(WEEKDAY, "loc-1")
        timestamps = [t["timestamp"] for t in txns]
        assert timestamps == sorted(timestamps)

    def test_weekend_busier(self):
        pos = MockSquarePOS()
        weekday_count = len(pos.fetch_transactions(WEEKDAY, "loc-1"))
        weekend_count = len(pos.fetch_transactions(WEEKEND, "loc-1"))
        assert weekend_count > weekday_count


class TestTimesheetConnector:
    def test_returns_punches(self):
        punches = MockTimesheet().fetch_punches(WEEKDAY, "loc-1")
        assert len(punches) == 3
        for p in punches:
            assert set(p) >= {"employee_id", "clock_in", "clock_out", "location_id", "wage"}
            assert p["clock_out"] > p["clock_in"]

    def test_weekend_has_extra_staff(self):
        ts = MockTimesheet()
        assert len(ts.fetch_punches(WEEKEND, "loc-1")) == 4


class TestRegistry:
    def test_get_pos_connector_default(self):
        assert isinstance(get_pos_connector(), MockSquarePOS)
        assert isinstance(get_pos_connector("mock_square"), MockSquarePOS)

    def test_get_timesheet_connector_default(self):
        assert isinstance(get_timesheet_connector(), MockTimesheet)

    def test_unknown_connector_raises(self):
        with pytest.raises(ValueError):
            get_pos_connector("nonexistent")
        with pytest.raises(ValueError):
            get_timesheet_connector("nonexistent")
