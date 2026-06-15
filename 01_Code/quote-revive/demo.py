"""Quote Revive — offline demo. Run: python demo.py

Simulates a quote sent 20 days ago moving through the full follow-up sequence
day by day, with a mock sender (nothing is actually sent).
"""

from datetime import date, timedelta

import engine


def main() -> int:
    start = date(2026, 6, 2)
    quote = engine.Quote("Q-1001", "Dana Reeves", 4800.0, sent_date=start)

    sender = engine._mock_sender_factory()
    print("Simulating 16 days of follow-up for a $4,800 quote to Dana Reeves:\n")
    for offset in range(0, 17):
        today = start + timedelta(days=offset)
        result = engine.run_cycle([quote], today=today, sender=sender)
        for a in result["actions"]:
            print(f"  day {offset:>2}: follow-up #{a.step} sent -> \"{a.message}\"")
        for h in result["handoffs"]:
            print(f"  day {offset:>2}: HANDOFF -> {h.message}")
            quote.status = "declined"  # stop after handoff for the demo

    print(f"\nTotal messages the mock sender recorded: {len(sender.sent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
