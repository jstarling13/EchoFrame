"""
Offline demo for the Shift Lens engine.

Renders the Foundry Coffee sample CSV through templates/shift_lens.html.j2 WITHOUT
calling Claude — the Pattern Note and One Thing below are canned so the template
can be previewed and the math (pandas) verified instantly.

  python demo_shift_lens.py

In production, main.py routes through products.py to
shift_lens_engine.generate_shift_lens_report(), which runs the same pandas +
Jinja2 path but sources the prose from Claude tool_use.
"""

from pathlib import Path
from shift_lens_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "shift_lens_sample_input.csv"

PROSE = {
    "pattern_note": (
        "The blended <b>32.6%</b> labor rate looks healthy — but it hides a clear daypart "
        "pattern: <b>mornings carry the business and late afternoons bleed it.</b> Every morning "
        "shift runs near 22% labor and throws off the bulk of weekly margin. After 2&nbsp;PM, foot "
        "traffic falls off a cliff while staffing stays flat at two baristas, so labor climbs to "
        "47% by afternoon and past <b>100%</b> in the weeknight evening — the only shift that loses "
        "money outright. Weekends repeat the shape on a smaller scale. The issue isn't wage rates; "
        "it's <b>hours scheduled against demand</b> in the back half of the day."
    ),
    "one_thing_title": "Close at 5 PM on weekdays and run the 2–5 PM block with one barista.",
    "one_thing_body": (
        "The weeknight evening shift is the only one on the board that <span class=\"dollar\">loses "
        "money</span> — about <span class=\"dollar\">$465/week</span> in labor against just "
        "<span class=\"dollar\">$360</span> in sales. Cutting it and dropping the slow weekday "
        "afternoon from two baristas to one removes roughly <span class=\"dollar\">$695/week</span> "
        "of labor — about <span class=\"dollar\">$3,000 a month</span>. You give up only the "
        "~$360/week of lowest-margin evening revenue, much of which shifts to earlier orders, for an "
        "estimated <span class=\"dollar\">net savings of ~$2,300 a month</span> with no change to "
        "your busy, profitable mornings."
    ),
}


def main():
    path = render_from_csv(CSV, prose=PROSE, is_sample=True)
    print(f"  shift-lens -> {path}")


if __name__ == "__main__":
    main()
