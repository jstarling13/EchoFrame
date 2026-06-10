"""Offline demo for Call Catch. python demo_call_catch.py"""
from pathlib import Path
from call_catch_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "call_catch_sample_input.csv"

PROSE = {
    "thread_meta": "Thread · Tue Jun 17, 2:14 PM · Caller (706) •••-4827",
    "missed_note": "✕ Missed call — no answer (line busy on another job)",
    "booked_note": "✓ Booked — $740 water-heater replacement",
    "bubbles": [
        {"dir": "out", "who": "Chattahoochee Plumbing", "auto": "AUTO · 2:15 PM",
         "text": "Hi, this is Chattahoochee Plumbing — sorry we missed your call! We're out on a job right now. "
                 "How can we help? Reply here and we'll get right back to you. 🔧", "time": "Delivered · 2:15 PM"},
        {"dir": "in", "who": "Caller", "text": "Hey — water heater is leaking all over my garage floor. Need "
         "someone out today if you can.", "time": "2:16 PM"},
        {"dir": "out", "who": "Chattahoochee Plumbing", "text": "Got it — we can have a tech to you between 4–6 PM "
         "today. What's the service address?", "time": "2:19 PM"},
        {"dir": "in", "who": "Caller", "text": "1142 Wynnton Rd. Thank you!!", "time": "2:20 PM"},
        {"dir": "out", "who": "Chattahoochee Plumbing", "text": "You're booked for 4–6 PM today. You'll get a text "
         "when our tech is on the way. See you soon! 👍", "time": "2:21 PM"},
    ],
    "one_thing_title": "Call Catch recovered 37% of your missed calls this month — about $8,420 in booked work.",
    "one_thing_body": (
        "You missed <span class=\"dollar\">38 calls</span> in June; every one got a text back inside a minute, and "
        "<span class=\"dollar\">14 callers</span> wrote back instead of dialing the next plumber. Those replies "
        "turned into <span class=\"dollar\">$8,420</span> of booked jobs that would otherwise have walked — for "
        "roughly the cost of a single service call. Most recoveries came from after-hours and \"line busy on "
        "another job\" misses, which is exactly when a Columbus homeowner with a leak keeps scrolling. Hold that "
        "37% recovery rate and Call Catch pays for itself many times over every month."
    ),
}


def main():
    print(f"  call-catch -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
