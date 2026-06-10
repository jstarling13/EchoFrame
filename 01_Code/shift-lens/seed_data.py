"""
Seed the Shift Lens database with shift definitions, employees, and a full week
of realistic POS transactions + time punches, then run the ETL pipeline.

Run:
    python seed_data.py                 # uses DATABASE_URL (SQLite by default)
    python seed_data.py --reset         # drop & recreate all tables first
"""

import sys
import random
from datetime import datetime, date, time, timedelta

from models.base import SessionLocal, create_all_tables, drop_all_tables
from models.employee import Employee
from models.shift_definition import ShiftDefinition
from service.shift_service import ShiftPLService
from logging_config import get_logger

logger = get_logger("seed")

LOCATION_ID = "columbus-main"

# Two shifts per day, 7 days a week.
SHIFT_BLOCKS = [
    ("Morning", time(6, 0), time(14, 0)),
    ("Afternoon", time(14, 0), time(22, 0)),
]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

EMPLOYEES = [
    ("EMP-001", "Alex Rivera", 15.00),
    ("EMP-002", "Bri Chen", 16.50),
    ("EMP-003", "Cory Diaz", 15.50),
    ("EMP-004", "Dana Patel", 18.00),
]


def seed_shift_definitions(session) -> list[ShiftDefinition]:
    defs = []
    for dow, day_name in enumerate(DAY_NAMES):
        for block_name, start, end in SHIFT_BLOCKS:
            defs.append(
                ShiftDefinition(
                    location_id=LOCATION_ID,
                    shift_name=f"{day_name} {block_name}",
                    day_of_week=dow,
                    start_time=start,
                    end_time=end,
                )
            )
    session.add_all(defs)

    for emp_id, name, wage in EMPLOYEES:
        session.merge(Employee(id=emp_id, name=name, base_wage=wage, location_id=LOCATION_ID))

    session.commit()
    logger.info("seeded %d shift definitions and %d employees", len(defs), len(EMPLOYEES))
    return defs


def generate_day(day: date) -> tuple[list[dict], list[dict]]:
    """Generate realistic transactions + punches for one day."""
    rng = random.Random(day.toordinal())  # deterministic per-date
    is_weekend = day.weekday() >= 5

    transactions = []
    order_seq = 1
    # Busier afternoons; weekends busier overall.
    for block_name, start, end in SHIFT_BLOCKS:
        base = 18 if block_name == "Afternoon" else 10
        count = int(base * (1.4 if is_weekend else 1.0))
        for _ in range(count):
            hour = rng.randint(start.hour, end.hour - 1)
            minute = rng.randint(0, 59)
            ts = datetime.combine(day, time(hour, minute))
            amount = round(rng.uniform(8.0, 65.0), 2)
            transactions.append({
                "timestamp": ts,
                "amount": amount,
                "order_id": f"ORD-{day.isoformat()}-{order_seq:03d}",
                "location_id": LOCATION_ID,
            })
            order_seq += 1

    # Labor: 2 employees morning, 2 afternoon; one straddles the boundary.
    punches = [
        {"employee_id": "EMP-001", "clock_in": datetime.combine(day, time(6, 0)),
         "clock_out": datetime.combine(day, time(14, 0)), "location_id": LOCATION_ID, "wage": 15.00},
        {"employee_id": "EMP-002", "clock_in": datetime.combine(day, time(10, 0)),
         "clock_out": datetime.combine(day, time(18, 0)), "location_id": LOCATION_ID, "wage": 16.50},
        {"employee_id": "EMP-003", "clock_in": datetime.combine(day, time(14, 0)),
         "clock_out": datetime.combine(day, time(22, 0)), "location_id": LOCATION_ID, "wage": 15.50},
    ]
    if is_weekend:
        punches.append(
            {"employee_id": "EMP-004", "clock_in": datetime.combine(day, time(16, 0)),
             "clock_out": datetime.combine(day, time(22, 0)), "location_id": LOCATION_ID, "wage": 18.00}
        )
    return transactions, punches


def main():
    reset = "--reset" in sys.argv

    if reset:
        logger.info("resetting database (drop + create)")
        drop_all_tables()
    create_all_tables()

    session = SessionLocal()
    try:
        shift_defs = seed_shift_definitions(session)
        service = ShiftPLService(session, shift_defs)

        # Seed the most recent full week (Mon-Sun) ending yesterday.
        today = date.today()
        last_monday = today - timedelta(days=today.weekday() + 7)

        for offset in range(7):
            day = last_monday + timedelta(days=offset)
            txns, punches = generate_day(day)
            totals = service.process_day(day, LOCATION_ID, txns, punches, target_labor_pct=30.0)
            print(f"{day} ({DAY_NAMES[day.weekday()]}): "
                  f"rev ${totals['total_revenue']:,.0f}, labor ${totals['total_labor']:,.0f} "
                  f"({totals['transaction_count']} txns)")

        print(f"\nSeeded week of {last_monday} for location '{LOCATION_ID}'.")
        print(f"Weekly report:  GET /api/weekly-report/{LOCATION_ID}?week_start={last_monday}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
