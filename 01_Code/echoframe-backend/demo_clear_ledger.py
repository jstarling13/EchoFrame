"""Offline demo for Clear Ledger (both tiers). python demo_clear_ledger.py"""
from pathlib import Path
from clear_ledger_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "clear_ledger_sample_input.csv"

PROSE = {
    "stage_quotes": [
        "\"Hi — just a quick heads-up that invoice INV-2103 ($1,875) slipped past its due date. A copy and pay link are below. Thanks for being a great client!\"",
        "\"Following up on INV-2089 ($2,420), now 14 days past due. Please remit by Friday or let us know if there's an issue with the invoice so we can resolve it.\"",
        "\"Final notice: INV-2041 ($6,480) is 30+ days past due. Payment is required within 5 business days to keep service active and avoid a late fee. We'd like to keep working together.\"",
    ],
    "method_note": (
        "Every open invoice is tracked from its due date and moved through the sequence automatically — "
        "<b>friendly at day 3, firm at day 14, final notice at day 30</b> — with messaging tuned to recover "
        "the balance while protecting the relationship. Most invoices clear at the friendly or firm stage and "
        "never need your attention. When one reaches final notice, goes silent, or comes back with a dispute, "
        "Clear Ledger flags it and hands it to you with the full contact history. This cycle, the sequence "
        "collected <b>$14,320</b> and pulled average days-to-pay from <b>44 down to 31</b>."
    ),
    "one_thing_title": "Push Summit Ridge Medical Plaza to final notice today — then call.",
    "one_thing_body": (
        "It's the oldest and largest balance on the ledger: <span class=\"dollar\">$6,480</span> at "
        "<span class=\"dollar\">52 days</span> overdue, more than a third of everything outstanding. Two "
        "automated nudges have gone unanswered, so it has crossed into human-handoff territory. Send the final "
        "notice this morning and follow it with a direct call to their office manager this afternoon. Recovering "
        "this one invoice clears <span class=\"dollar\">37%</span> of your total overdue and removes the account "
        "most likely to age into a write-off."
    ),
}


def main():
    for tier in ("starter", "growth"):
        print(f"  {tier:<8} -> {render_from_csv(CSV, tier=tier, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
