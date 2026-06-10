"""
Offline demo for the Rival Scan HTML engine.

Renders the Tony's Brick Oven sample CSV through templates/rival_scan.html.j2
WITHOUT calling Claude — the analysis prose below is canned so the template can be
previewed and the math (pandas) verified instantly.

  python demo_rival_scan_html.py

(The older demo_rival_scan.py produced the legacy .docx sample; this is the new
HTML pipeline that matches Auto Ledger / Rate Watch.)

In production, main.py routes through products.py to
rival_scan_engine.generate_rival_scan_report(), which runs the same pandas +
Jinja2 path but sources the prose from Claude tool_use.
"""

from pathlib import Path
from rival_scan_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "rival_scan_sample_input.csv"

PROSE = {
    "what_moved": [
        {"tone": "threat",
         "text": "<b>Marco's slashed online pricing.</b> Large 1-topping dropped to $9.99 with code "
                 "PIZZA10 — now undercuts you by $6.00 on delivery apps."},
        {"tone": "watch",
         "text": "<b>Mellow Mushroom raised base + launched a bundle.</b> Large specialty up $1.00 to "
                 "$18.50, paired with a \"2-for-$24 cheese\" promo running through 6/15."},
        {"tone": "opportunity",
         "text": "<b>Fountain City's new threshold plays to you.</b> Their \"free garlic knots over $25\" "
                 "kicks in above your ~$25.50 average ticket — easy to out-message."},
        {"tone": "neutral",
         "text": "<b>Reviews shifting.</b> 14 new Google reviews across rivals this week; Mellow "
                 "Mushroom's rating slipped 4.4 → 4.3."},
    ],
    "one_thing_title": "Counter Marco's $9.99 online push — don't match it.",
    "one_thing_body": (
        "Marco's loss-leader targets price-sensitive online orders, not your dine-in base. Matching "
        "$9.99 torches margin; ignoring it cedes weekday delivery. Launch a \"Tuesday Online-Only "
        "Large 1-Topping — $11.99\" fenced to your own app and web ordering, capped at one per order."
    ),
    "one_thing_steps": [
        "Add the $11.99 Tuesday code to your online menu and pin it to the app home screen.",
        "Push it once to your SMS/email list framed as \"skip the apps, order direct.\"",
        "Leave dine-in and your $15.99 everyday price untouched — this is a fence, not a price cut.",
    ],
    "one_thing_impact": (
        "defends ~$1,150/month in at-risk online revenue (≈35 weekday online orders/wk × $15.99, the "
        "cohort most likely to chase Marco's code)."
    ),
    "one_thing_risk": (
        "Cannibalization if un-fenced. Keep it online-only and one-per-order so walk-in traffic "
        "doesn't trade down."
    ),
}


def main():
    path = render_from_csv(CSV, prose=PROSE, is_sample=True)
    print(f"  rival-scan -> {path}")


if __name__ == "__main__":
    main()
