"""Offline demo for Drive Pay. python demo_drive_pay.py"""
from pathlib import Path
from products.drive_pay.drive_pay_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "drive_pay_sample_input.csv"

PROSE = {
    "thread_meta": "Thread · Thu Jun 19, 4:38 PM · Customer (706) •••-3162",
    "ready_note": "RO #4471 marked Ready for Pickup — 2018 Chevy Silverado · $842.50",
    "paid_note": "✓ Paid $842.50 · Visa ••4419 · Apple Pay · 2m 41s after text",
    "bubbles": [
        {"dir": "out", "who": "Cross Creek Auto", "auto": "AUTO · 4:38 PM",
         "text": "Hi Dave — your 2018 Silverado is all done at Cross Creek Auto! 🔧 Your total is $842.50 (brakes "
                 "+ front rotors). Tap to pay and we'll pull it up front with the keys in it: crosscreekauto.pay/4471",
         "time": "Delivered · 4:38 PM"},
        {"dir": "in", "who": "Customer", "text": "Perfect, on my way now. Paying it right now.", "time": "4:40 PM"},
        {"dir": "out", "who": "Cross Creek Auto", "auto": "AUTO · 4:41 PM",
         "text": "Payment received — thanks Dave! Your Silverado is out front, keys are in it. No stop at the "
                 "counter needed. Drive safe! 🚗", "time": "Delivered · 4:41 PM"},
    ],
    "one_thing_title": "Turn on pay-before-release for tickets over $500 — it would have pulled ~$5,100 forward this month.",
    "one_thing_body": (
        "Drive Pay collected <span class=\"dollar\">$46,180</span> in June, and <span class=\"dollar\">85%</span> of "
        "it landed before the car left the lot. But the <span class=\"dollar\">13 invoices</span> that weren't paid "
        "at pickup averaged six days to collect — and one $1,180 transmission job is now <span class=\"dollar\">40 "
        "days past due</span> after the customer drove off. Nine of those thirteen were over $500. Switch on "
        "\"confirm payment before keys\" for tickets above $500 and most of that $6,920 collects at the counter "
        "instead of aging into receivables — starting with the job that's already in collections."
    ),
}


def main():
    print(f"  drive-pay -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
