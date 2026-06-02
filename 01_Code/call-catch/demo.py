"""Call Catch — offline demo. Run: python demo.py"""

from datetime import datetime

import engine


def main() -> int:
    cc = engine.CallCatch("Reliable Heating & Air")

    calls = [
        ("+17065550101", datetime(2026, 6, 2, 10, 30)),   # Tue mid-morning → business hours
        ("+17065550102", datetime(2026, 6, 2, 19, 45)),   # Tue evening → after hours
        ("+17065550101", datetime(2026, 6, 2, 10, 32)),   # repeat caller → deduped (no 2nd text)
        ("+17065550103", datetime(2026, 6, 6, 13, 0)),    # Saturday → after hours (closed)
    ]

    print("Incoming missed calls:\n")
    for number, when in calls:
        e = cc.handle_missed_call(number, occurred_at=when)
        tag = "after-hours" if e.after_hours else "business-hours"
        status = "TEXT SENT" if e.delivered else "deduped (no text)"
        print(f"  {when:%a %H:%M} {number} [{tag}] -> {status}")
        if e.delivered:
            print(f"      \"{e.message_sent}\"")

    print()
    db = cc.dashboard()
    print(f"Dashboard: {db['total_missed_calls']} missed calls, {db['texts_sent']} texts sent, "
          f"{db['after_hours_calls']} after-hours, {db['unique_callers']} unique callers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
