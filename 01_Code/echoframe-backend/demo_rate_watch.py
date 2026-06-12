"""
Offline demo for the Rate Watch engine.

Renders the Magnolia Lane sample CSV through templates/rate_watch.html.j2 for both
tiers (core / pro) WITHOUT calling Claude — the per-vendor actions and narrative
below are canned so the template can be previewed and the math (pandas) verified
instantly.

  python demo_rate_watch.py

In production, main.py routes through products.py to
rate_watch_engine.generate_rate_watch_report(), which runs the exact same pandas +
Jinja2 path but sources actions/prose from Claude tool_use.
"""

from pathlib import Path
from products.rate_watch.rate_watch_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "rate_watch_sample_input.csv"

# Canned prose — the shape Claude returns from write_rate_watch_report.
# `index` matches the CSV order (0 = Merchant Card Processing, …).
PROSE = {
    "vendors": [
        {"index": 0, "action": "Renegotiate now"},
        {"index": 1, "action": "Benchmark before renewal"},
        {"index": 2, "action": "Downgrade tier"},
        {"index": 3, "action": "Re-bid at renewal"},
        {"index": 4, "action": "Re-shop policy"},
        {"index": 5, "action": "Switch plan"},
        {"index": 6, "action": "Re-bid contract"},
        {"index": 7, "action": "Monitor usage"},
        {"index": 8, "action": "Hold"},
        {"index": 9, "action": "Hold"},
    ],
    "benchmarking_note": (
        "Each vendor is compared against current Columbus, GA market rates for a salon of "
        "similar size and volume — drawn from local vendor quotes, regional service averages, "
        "and published merchant-services and commercial-lease data. <b>Over / Under</b> is the "
        "annualized dollar gap versus that benchmark: a prioritized starting point, not a "
        "guaranteed saving. Eight of ten vendors are priced above market, with the recoverable "
        "spread concentrated in card processing and the lease. The two at-market vendors need no "
        "action this cycle."
    ),
    "one_thing_title": "Renegotiate merchant card processing before the July 15 renewal.",
    "one_thing_body": (
        "It's the single largest gap on the list — a <span class=\"dollar\">2.95%</span> "
        "effective rate against a <span class=\"dollar\">2.45%</span> local-market rate on "
        "roughly $46K/month in card volume, worth about <span class=\"dollar\">$3,480 a year</span>. "
        "The contract auto-renews July 15, which is your leverage: ask for interchange-plus "
        "pricing or bring a competing quote to your processor before it locks for another term. "
        "One conversation recovers nearly a third of the total overpayment."
    ),
}


def main():
    for tier in ("core", "pro"):
        path = render_from_csv(CSV, tier=tier, prose=PROSE, is_sample=True)
        print(f"  {tier:<5} -> {path}")


if __name__ == "__main__":
    main()
