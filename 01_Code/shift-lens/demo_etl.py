"""
Offline demo of the full Shift Lens ETL pipeline.
Run: python demo_etl.py
"""

from datetime import datetime, date, time
import pandas as pd
from etl.shift_mapper import ShiftMapper
from etl.labor_allocator import LaborAllocator
from models.shift_definition import ShiftDefinition
from etl.ingestion import ingest_from_dict
import engine

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

def main():
    print("=" * 80)
    print("SHIFT LENS — FULL ETL PIPELINE DEMO (No Database)")
    print("=" * 80)
    print()

    shift_definitions = [
        make_shift_def(1, "Monday Morning", 0, time(6, 0), time(14, 0)),
        make_shift_def(2, "Monday Afternoon", 0, time(14, 0), time(22, 0)),
        make_shift_def(3, "Tuesday Morning", 1, time(6, 0), time(14, 0)),
        make_shift_def(4, "Tuesday Afternoon", 1, time(14, 0), time(22, 0)),
    ]

    raw_transactions = [
        {"timestamp": datetime(2024, 1, 15, 8, 30), "amount": 125.50, "order_id": "ORD-001", "location_id": "columbus-main"},
        {"timestamp": datetime(2024, 1, 15, 12, 15), "amount": 89.75, "order_id": "ORD-002", "location_id": "columbus-main"},
        {"timestamp": datetime(2024, 1, 15, 16, 45), "amount": 200.00, "order_id": "ORD-003", "location_id": "columbus-main"},
        {"timestamp": datetime(2024, 1, 15, 20, 30), "amount": 150.25, "order_id": "ORD-004", "location_id": "columbus-main"},
    ]

    raw_punches = [
        {"employee_id": "EMP-001", "clock_in": datetime(2024, 1, 15, 6, 0), "clock_out": datetime(2024, 1, 15, 14, 0), "location_id": "columbus-main", "wage": 15.00},
        {"employee_id": "EMP-002", "clock_in": datetime(2024, 1, 15, 10, 0), "clock_out": datetime(2024, 1, 15, 18, 0), "location_id": "columbus-main", "wage": 16.00},
        {"employee_id": "EMP-003", "clock_in": datetime(2024, 1, 15, 14, 0), "clock_out": datetime(2024, 1, 15, 22, 0), "location_id": "columbus-main", "wage": 15.50},
    ]

    print("STEP 1: INGEST RAW DATA")
    print("-" * 80)
    txn_df, punch_df = ingest_from_dict(raw_transactions, raw_punches)
    print(f"Ingested {len(txn_df)} transactions")
    print(f"Ingested {len(punch_df)} time punches")
    print()

    print("STEP 2: MAP TRANSACTIONS TO SHIFTS")
    print("-" * 80)
    mapper = ShiftMapper(shift_definitions)
    shift_date = date(2024, 1, 15)
    txn_mapped = mapper.map_transactions_to_shifts(txn_df, shift_date, "columbus-main")
    print("Transaction mappings:")
    print(txn_mapped.to_string(index=False))
    print()

    print("STEP 3: ALLOCATE LABOR ACROSS SHIFTS")
    print("-" * 80)
    allocator = LaborAllocator(shift_definitions)
    labor_mapped = allocator.allocate_labor_across_shifts(punch_df, shift_date, "columbus-main")
    print("Labor allocations:")
    print(labor_mapped.to_string(index=False))
    print()

    print("STEP 4: AGGREGATE BY SHIFT")
    print("-" * 80)

    shift_aggregates = {}
    for _, row in txn_mapped.iterrows():
        shift_id = row["shift_definition_id"]
        if shift_id not in shift_aggregates:
            shift_aggregates[shift_id] = {"revenue": 0, "labor": 0}
        shift_aggregates[shift_id]["revenue"] += row["amount"] if row["allocation_pct"] > 0 else 0

    for _, row in labor_mapped.iterrows():
        shift_id = row["shift_definition_id"]
        if shift_id not in shift_aggregates:
            shift_aggregates[shift_id] = {"revenue": 0, "labor": 0}
        shift_aggregates[shift_id]["labor"] += row["labor_cost"]

    shifts_for_report = []
    for shift_def in shift_definitions:
        if shift_def.day_of_week == shift_date.weekday():
            agg = shift_aggregates.get(shift_def.id, {"revenue": 0, "labor": 0})
            shifts_for_report.append(
                engine.Shift(
                    label=shift_def.shift_name,
                    revenue=agg["revenue"],
                    labor_cost=agg["labor"],
                )
            )

    for shift in shifts_for_report:
        print(f"{shift.label}: Revenue ${shift.revenue:,.2f}, Labor ${shift.resolved_labor_cost():,.2f}")
    print()

    print("STEP 5: COMPUTE P&L & GENERATE REPORT")
    print("-" * 80)
    report = engine.analyze_week(shifts_for_report, target_labor_pct=30.0)
    report_text = engine.render_report_text(report)
    print(report_text)
    print()

    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
