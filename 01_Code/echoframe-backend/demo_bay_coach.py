"""Offline demo for Bay Coach. python demo_bay_coach.py"""
from pathlib import Path
from bay_coach_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "bay_coach_sample_input.csv"

PROSE = {
    "vstat": (
        "No record of <b>brake fluid</b>, <b>coolant</b>, <b>spark plugs</b>, or <b>transmission service</b> in "
        "92K miles. Battery is <b>5 yrs old</b>. Customer averages <b>~13,200 mi/yr</b> — so the next visit is "
        "likely <b>11–12 months out</b>. That makes today the right write-up to surface the 90K-mile interval "
        "items rather than wait."
    ),
    "services": [
        {"why": "Toyota specifies iridium plugs at 90K–100K mi and none are on file. At 92K the car is in-window; "
                "replacing now heads off the misfire that takes out an ignition coil."},
        {"why": "No fluid service in 92K mi on record, last brake job 2+ yrs ago. Brake fluid absorbs moisture, "
                "lowering boil point and corroding ABS parts. Due every 3 yrs / 30K mi."},
        {"why": "Factory long-life coolant is rated to ~100K mi / 10 yrs and has never been serviced. At 92K it's "
                "near end of life — refreshing now protects the water pump ahead of summer heat."},
        {"why": "Battery installed Jun 2021 — 5 yrs old, past the 4–5 yr Georgia-heat lifespan. Replacing on this "
                "visit beats a no-start call in July; confirm with a load test first."},
        {"why": "Not in the history on file; both are 30K-mi items, so each is ~3 intervals overdue. Low-cost "
                "add-on the customer can see and approve on the spot."},
    ],
    "method_note": (
        "Bay Coach reads the vehicle's <b>year/make/model, current odometer, and every service on this shop's own "
        "history</b>, compares them to the manufacturer's schedule, and surfaces only what's <b>actually due for "
        "this car</b> — not a generic upsell list — with a plain-language \"why now\" the advisor can read at the counter."
    ),
    "one_thing_title": "Lead with the spark plugs — it's the one item that's clearly overdue and easiest to say yes to.",
    "one_thing_body": (
        "Of everything flagged, the <span class=\"dollar\">$289 spark plug replacement</span> is the highest-value, "
        "most defensible recommendation: it's <span class=\"dollar\">2,000+ miles into the factory window</span> "
        "with no record of ever being done, and the failure it prevents — a misfire that takes out an ignition coil "
        "— costs the customer far more later. Present it first, in plain terms (\"your plugs are due and we're "
        "already in here\"), and pair it with the <span class=\"dollar\">$129 brake fluid flush</span> as a natural "
        "add-on. At this shop's <span class=\"dollar\">61% acceptance rate</span>, leading with these two adds "
        "roughly <span class=\"dollar\">$255 to this single ticket</span>."
    ),
}


def main():
    print(f"  bay-coach -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
