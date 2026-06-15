"""Shift Lens — offline demo.  Run:  python demo.py"""

import engine


def main() -> int:
    shifts = [
        engine.Shift("Mon Lunch",  revenue=1200, labor_hours=28, avg_wage=15),   # ~35%
        engine.Shift("Mon Dinner", revenue=3200, labor_cost=820),                # ~26% healthy
        engine.Shift("Tue Lunch",  revenue=600,  labor_hours=26, avg_wage=15),   # ~65% bad
        engine.Shift("Tue Dinner", revenue=2800, labor_cost=760),                # healthy
        engine.Shift("Wed Lunch",  revenue=300,  labor_cost=420),                # loses money
        engine.Shift("Sat Dinner", revenue=5200, labor_cost=1300),              # best, 25%
    ]
    report = engine.analyze_week(shifts)
    print(engine.render_report_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
