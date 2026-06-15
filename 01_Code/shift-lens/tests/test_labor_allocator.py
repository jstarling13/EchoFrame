"""Tests for the labor allocator (split shifts)."""

import pytest
from datetime import datetime, date, time
from decimal import Decimal
import pandas as pd
from etl.labor_allocator import LaborAllocator
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

class TestLaborAllocator:
    @pytest.fixture
    def allocator(self):
        shifts = [
            make_shift_def(1, "Morning", 0, time(6, 0), time(14, 0)),
            make_shift_def(2, "Afternoon", 0, time(14, 0), time(22, 0)),
        ]
        return LaborAllocator(shifts)

    def test_punch_within_single_shift(self, allocator):
        """Punch entirely within one shift should allocate fully to that shift."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 6, 0),
                "clock_out": datetime(2024, 1, 15, 14, 0),
                "wage": 15.00,
                "id": 1,
            }
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        assert result.iloc[0]["shift_definition_id"] == 1
        assert result.iloc[0]["hours"] == 8.0
        assert result.iloc[0]["labor_cost"] == 120.0

    def test_punch_spanning_two_shifts(self, allocator):
        """Punch spanning two shifts should split labor proportionally."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 10, 0),
                "clock_out": datetime(2024, 1, 15, 18, 0),
                "wage": 20.00,
                "id": 1,
            }
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 2
        # 10:00-14:00 = 4 hours in morning shift
        morning_row = result[result["shift_definition_id"] == 1].iloc[0]
        assert morning_row["hours"] == 4.0
        assert morning_row["labor_cost"] == 80.0

        # 14:00-18:00 = 4 hours in afternoon shift
        afternoon_row = result[result["shift_definition_id"] == 2].iloc[0]
        assert afternoon_row["hours"] == 4.0
        assert afternoon_row["labor_cost"] == 80.0

    def test_punch_partial_overlap(self, allocator):
        """Punch partially overlapping shifts."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 12, 0),
                "clock_out": datetime(2024, 1, 15, 16, 0),
                "wage": 15.00,
                "id": 1,
            }
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 2
        # 12:00-14:00 = 2 hours in morning
        morning_row = result[result["shift_definition_id"] == 1].iloc[0]
        assert morning_row["hours"] == 2.0
        assert morning_row["labor_cost"] == 30.0

        # 14:00-16:00 = 2 hours in afternoon
        afternoon_row = result[result["shift_definition_id"] == 2].iloc[0]
        assert afternoon_row["hours"] == 2.0
        assert afternoon_row["labor_cost"] == 30.0

    def test_punch_no_overlap(self, allocator):
        """Punch outside shift hours should have no allocation."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 3, 0),
                "clock_out": datetime(2024, 1, 15, 4, 0),
                "wage": 15.00,
                "id": 1,
            }
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 0

    def test_multiple_employees(self, allocator):
        """Multiple employees should each be allocated."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 6, 0),
                "clock_out": datetime(2024, 1, 15, 14, 0),
                "wage": 15.00,
                "id": 1,
            },
            {
                "employee_id": "EMP-002",
                "clock_in": datetime(2024, 1, 15, 14, 0),
                "clock_out": datetime(2024, 1, 15, 22, 0),
                "wage": 16.00,
                "id": 2,
            },
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 2
        assert result.iloc[0]["employee_id"] == "EMP-001"
        assert result.iloc[1]["employee_id"] == "EMP-002"

    def test_wage_application(self, allocator):
        """Labor cost should be hours × wage."""
        punches = pd.DataFrame([
            {
                "employee_id": "EMP-001",
                "clock_in": datetime(2024, 1, 15, 6, 0),
                "clock_out": datetime(2024, 1, 15, 10, 0),
                "wage": 20.00,
                "id": 1,
            }
        ])
        result = allocator.allocate_labor_across_shifts(punches, date(2024, 1, 15), "columbus-main")

        assert len(result) == 1
        assert result.iloc[0]["hours"] == 4.0
        assert result.iloc[0]["labor_cost"] == 80.0
