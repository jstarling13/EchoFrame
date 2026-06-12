"""Offline demo for the Revenue Suite (combines the three product sample CSVs).
python demo_revenue_suite.py"""
from pathlib import Path
from products.revenue_suite.revenue_suite_engine import render_from_csvs

OUT = Path(__file__).resolve().parent / "demo_output"
CC = OUT / "call_catch_sample_input.csv"
QR = OUT / "quote_revive_sample_input.csv"
CL = OUT / "clear_ledger_sample_input.csv"

META = {"Business Name": "Chattahoochee Home Services LLC", "Month": "June 2026", "Location": "Columbus GA"}

PROSE = {
    "intro_note": (
        "Across all three tools, the suite put <b>$64,640</b> back on the table this month — money that "
        "would otherwise have leaked from missed calls, cold quotes, and unpaid invoices."
    ),
    "suite_note": (
        "Every dollar you're owed leaks out at one of three points — the call you missed, the quote that went "
        "cold, or the invoice that never got paid. The <b>Revenue Suite</b> plugs all three on one bill: Call "
        "Catch texts back missed callers in under a minute, Quote Revive works your ghosted quotes on a timed "
        "sequence, and Clear Ledger escalates overdue invoices from friendly nudge to final notice. One login, "
        "one report, priority support."
    ),
    "one_thing_title": "Call the $31,200 metal-roof quote — the biggest single lever across all three tools.",
    "one_thing_body": (
        "Quote Revive flagged a <span class=\"dollar\">$31,200</span> standing-seam job that has opened both "
        "follow-ups but hasn't replied — the largest engaged opportunity anywhere in the suite this month. "
        "Automation has done its part; a two-minute owner call now is worth more than another text. Closing "
        "this one quote would add more than <span class=\"dollar\">double</span> this month's Clear Ledger "
        "collections, on top of the <span class=\"dollar\">$64,640</span> already recovered."
    ),
}


def main():
    print(f"  revenue-suite -> {render_from_csvs(CC, QR, CL, prose=PROSE, meta=META, is_sample=True)}")


if __name__ == "__main__":
    main()
