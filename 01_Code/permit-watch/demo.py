"""Permit Watch — offline demo.  Run:  python demo.py"""

from datetime import date, timedelta

import engine


def main() -> int:
    today = date.today()
    items = [
        engine.ComplianceItem("Vehicle registration", "registration",
                              today - timedelta(days=3), entity="Van 12", identifier="GA ABC123"),
        engine.ComplianceItem("DOT inspection", "inspection",
                              today + timedelta(days=5), entity="Truck 3"),
        engine.ComplianceItem("Business license", "license",
                              today + timedelta(days=22), identifier="COL-2024-558"),
        engine.ComplianceItem("Liability insurance", "insurance",
                              today + timedelta(days=48), entity="Business-wide"),
        engine.ComplianceItem("Vehicle registration", "registration",
                              today + timedelta(days=210), entity="Van 9"),
    ]
    db = engine.build_dashboard(items, today=today)
    print(engine.render_alert_digest(db))
    print()
    print(f"Dashboard counts: {db['counts']}")
    print(f"Entities tracked: {list(db['by_entity'].keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
