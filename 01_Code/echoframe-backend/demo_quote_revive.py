"""Offline demo for Quote Revive. python demo_quote_revive.py"""
from pathlib import Path
from products.quote_revive.quote_revive_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "quote_revive_sample_input.csv"

PROSE = {
    "steps": [
        {"message": "Hi Dana, it's the team at Chattahoochee Ridge Roofing. Just making sure the estimate for "
                    "your <span class=\"q\">architectural shingle re-roof ($14,800)</span> landed okay. Happy to "
                    "walk through any line item — want me to hold your spot on next month's schedule?",
         "goal": "confirm receipt, stay warm, low pressure."},
        {"message": "A quick nudge on your roof estimate. A few neighbors on the same street booked ahead of "
                    "storm season, so material lead times are tightening. Your <span class=\"q\">quoted price is "
                    "locked for 30 days</span> — reply here and I'll get you on the calendar before rates move.",
         "goal": "add urgency &amp; social proof, reassure on price."},
        {"message": "Last check-in, Dana — I don't want to keep crowding your inbox. If the timing isn't right, "
                    "no problem at all; just reply <span class=\"q\">\"later\"</span> and I'll close the file. If "
                    "you're still considering it, I can offer a <span class=\"q\">free re-inspection</span> before "
                    "the quote expires Friday.",
         "goal": "the \"breakup\" — forces a yes / no / later."},
    ],
    "method_note": (
        "When a quote you've sent goes quiet, Quote Revive starts a <b>three-touch sequence on its own</b> — a "
        "friendly Day 2 text, a Day 7 email with light urgency, and a Day 14 \"breakup\" that forces a clean yes, "
        "no, or later. Replies route straight back to you; quotes that say no are closed so you stop chasing them. "
        "<b>Days Cold</b> counts from the date the quote was sent, and the price stays locked through the sequence "
        "so the customer never feels penalized for taking their time."
    ),
    "one_thing_title": "Call Q-1053 — the $31,200 standing-seam metal roof — personally this week.",
    "one_thing_body": (
        "It's the single largest live opportunity on the board: a <span class=\"dollar\">$31,200</span> new-build "
        "job in Harris County that has <span class=\"dollar\">opened both follow-ups</span> but hasn't replied, and "
        "it's 35 days cold with one touch left before the sequence ends. A quote that size and that engaged is past "
        "what automation should carry alone — a two-minute personal call from the owner, before the Day 14 breakup "
        "goes out, is worth more than ten more texts. Reactivating this one quote would more than double the revenue "
        "recovered this cycle."
    ),
}


def main():
    print(f"  quote-revive -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
