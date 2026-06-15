"""Sample data fixtures for testing."""

from datetime import datetime, date, time
from typing import List, Dict, Any

def sample_shifts() -> List[Dict[str, Any]]:
    """Sample shift definitions."""
    return [
        {
            "id": 1,
            "location_id": "columbus-main",
            "shift_name": "Monday Morning",
            "day_of_week": 0,
            "start_time": time(6, 0),
            "end_time": time(14, 0),
        },
        {
            "id": 2,
            "location_id": "columbus-main",
            "shift_name": "Monday Afternoon",
            "day_of_week": 0,
            "start_time": time(14, 0),
            "end_time": time(22, 0),
        },
        {
            "id": 3,
            "location_id": "columbus-main",
            "shift_name": "Tuesday Morning",
            "day_of_week": 1,
            "start_time": time(6, 0),
            "end_time": time(14, 0),
        },
    ]

def sample_transactions() -> List[Dict[str, Any]]:
    """Sample POS transactions for Monday, 2024-01-15."""
    return [
        {
            "timestamp": datetime(2024, 1, 15, 8, 30),
            "amount": 125.50,
            "order_id": "ORD-001",
            "location_id": "columbus-main",
        },
        {
            "timestamp": datetime(2024, 1, 15, 12, 15),
            "amount": 89.75,
            "order_id": "ORD-002",
            "location_id": "columbus-main",
        },
        {
            "timestamp": datetime(2024, 1, 15, 16, 45),
            "amount": 200.00,
            "order_id": "ORD-003",
            "location_id": "columbus-main",
        },
        {
            "timestamp": datetime(2024, 1, 15, 20, 30),
            "amount": 150.25,
            "order_id": "ORD-004",
            "location_id": "columbus-main",
        },
    ]

def sample_punches() -> List[Dict[str, Any]]:
    """Sample time punches for Monday, 2024-01-15."""
    return [
        {
            "employee_id": "EMP-001",
            "clock_in": datetime(2024, 1, 15, 6, 0),
            "clock_out": datetime(2024, 1, 15, 14, 0),
            "location_id": "columbus-main",
            "wage": 15.00,
        },
        {
            "employee_id": "EMP-002",
            "clock_in": datetime(2024, 1, 15, 10, 0),
            "clock_out": datetime(2024, 1, 15, 18, 0),
            "location_id": "columbus-main",
            "wage": 16.00,
        },
        {
            "employee_id": "EMP-003",
            "clock_in": datetime(2024, 1, 15, 14, 0),
            "clock_out": datetime(2024, 1, 15, 22, 0),
            "location_id": "columbus-main",
            "wage": 15.50,
        },
    ]
