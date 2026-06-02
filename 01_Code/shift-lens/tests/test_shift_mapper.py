"""Tests for the shift mapper algorithm."""

import pytest
from datetime import datetime, date, time
import pandas as pd
from etl.shift_mapper import ShiftMapper
from models.shift_definition import ShiftDefinition

def make_shift_def(shift_id, name, day, start, end):
    """Helper to create a ShiftDefinition."""
    s = ShiftDefinition()
    s.id = shift_id
    s.shift_name = name
    s.day_of_week = day
    s.start_time = start
    s.end_time = end
    s.location_id = "columbus-main"
    return s

class TestShiftMapper:
    @pytest.fixture
    def mapper(self):
        shifts = [
            make_shift_def(1, "Morning", 0, time(6, 0), time(14, 0)),
            make_shift_def(2, "Afternoon", 0, time(14, 0), time(22, 0)),
            make_shift_def(3, "Night", 0, time(22, 0), time(6, 0)),
        ]
        return ShiftMapper(shifts)

    def test_transaction_in_shift(self, mapper):
        """Transaction during shift hours should map to that shift."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 8, 30), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        assert result.iloc[0]["shift_definition_id"] == 1
        assert result.iloc[0]["allocation_pct"] == 1.0

    def test_transaction_at_shift_boundary(self, mapper):
        """Transaction at shift boundary (14:00) should go to afternoon shift."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 14, 0), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        assert result.iloc[0]["shift_definition_id"] == 2

    def test_transaction_between_shifts(self, mapper):
        """Transaction between shifts should go to nearest shift."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 13, 0), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        # 13:00 is 1 hour from morning end (14:00), so should map to morning
        assert result.iloc[0]["shift_definition_id"] == 1

    def test_overnight_shift(self, mapper):
        """Transaction in overnight shift (22:00-6:00) should map correctly."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 23, 30), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        assert result.iloc[0]["shift_definition_id"] == 3

    def test_transaction_far_from_shift_maps_to_nearest(self, mapper):
        """Per the 'nearest shift' rule, an off-hours txn still maps to the only shift."""
        mapper_limited = ShiftMapper([
            make_shift_def(1, "Morning", 0, time(8, 0), time(10, 0)),
        ])
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 3, 0), "amount": 100, "id": 1},
        ])
        result = mapper_limited.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        # Only one shift defined for the day -> nearest-shift assigns it there.
        assert result.iloc[0]["shift_definition_id"] == 1
        assert result.iloc[0]["allocation_pct"] == 1.0

    def test_multiple_transactions(self, mapper):
        """Multiple transactions should all be mapped."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 8, 0), "amount": 100, "id": 1},
            {"timestamp": datetime(2024, 1, 15, 15, 0), "amount": 200, "id": 2},
            {"timestamp": datetime(2024, 1, 15, 23, 0), "amount": 150, "id": 3},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "columbus-main")

        assert len(result) == 3
        assert result.iloc[0]["shift_definition_id"] == 1
        assert result.iloc[1]["shift_definition_id"] == 2
        assert result.iloc[2]["shift_definition_id"] == 3

    def test_wrong_location(self, mapper):
        """No shifts for that location -> txn retained but UNALLOCATED (revenue never dropped)."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 15, 8, 0), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 15), "other-location")

        assert len(result) == 1
        assert result.iloc[0]["shift_definition_id"] is None
        assert result.iloc[0]["allocation_pct"] == 0.0

    def test_wrong_day_of_week(self, mapper):
        """No shifts defined for that day -> txn is kept but flagged UNALLOCATED (never dropped)."""
        txns = pd.DataFrame([
            {"timestamp": datetime(2024, 1, 16, 8, 0), "amount": 100, "id": 1},
        ])
        result = mapper.map_transactions_to_shifts(txns, date(2024, 1, 16), "columbus-main")

        assert len(result) == 1
        # No shifts defined for Tuesday, so revenue is retained but unallocated.
        assert result.iloc[0]["shift_definition_id"] is None
        assert result.iloc[0]["allocation_pct"] == 0.0
