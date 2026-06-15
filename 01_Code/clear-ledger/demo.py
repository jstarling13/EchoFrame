"""Clear Ledger — offline demo. Run: python demo.py"""

from datetime import date, timedelta

import engine


def main() -> int:
    today = date(2026, 6, 2)
    invoices = [
        engine.Invoice("INV-201", "Dana Reeves", 1800, due_date=today - timedelta(days=2)),
        engine.Invoice("INV-202", "Cyrus Bell", 950, due_date=today - timedelta(days=10),
                       reminders_sent=1),
        engine.Invoice("INV-203", "Mara Quinn", 4200, due_date=today - timedelta(days=35),
                       reminders_sent=4),
        engine.Invoice("INV-204", "Owen Tate", 600, due_date=today + timedelta(days=5)),  # not due
        engine.Invoice("INV-205", "Paid Co", 300, due_date=today - timedelta(days=20),
                       status="paid"),
    ]

    result = engine.run_cycle(invoices, today=today)

    print(f"Clear Ledger cycle for {result['date']}")
    print(f"AR summary: {result['ar_summary']}")
    print()
    print(f"Reminders sent ({result['reminders_sent']}):")
    for a in result["actions"]:
        print(f"  • {a.invoice_id} step {a.step} ({a.days_overdue}d overdue): {a.message}")
    print()
    print(f"Handoffs ({len(result['handoffs'])}):")
    for h in result["handoffs"]:
        print(f"  • {h.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
