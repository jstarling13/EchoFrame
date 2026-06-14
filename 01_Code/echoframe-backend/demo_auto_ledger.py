"""
Offline demo for the Auto Ledger engine.

Renders the Blue Ridge sample CSV through templates/auto_ledger.html.j2 for all
THREE tiers (starter / growth / pro) WITHOUT calling Claude — the per-transaction
categories and narrative below are canned so the template can be previewed and the
math (pandas) verified instantly.

  python demo_auto_ledger.py

In production, main.py calls engine.generate_auto_ledger_report(), which runs the
exact same pandas + Jinja2 path but sources categories/prose from Claude tool_use.
"""

from pathlib import Path
from products.auto_ledger.auto_ledger_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "auto_ledger_sample_input.csv"

# Canned prose — the shape Claude returns from the write_auto_ledger_report tool.
PROSE = {
    "transactions": [
        {"index": 0, "category": "Service Revenue",
         "what_it_was": "Customer card payments for 9 completed jobs, batched by your field-service software.",
         "why_category": "Money in from selling your core service, so it lands in Service Revenue — not “Other Income.”"},
        {"index": 1, "category": "COGS — Equipment",
         "what_it_was": "A 4-ton condenser and coil for the Whitesville Rd install.",
         "why_category": "Equipment resold to a customer on a job, so it's Cost of Goods Sold — it offsets that job's revenue, not overhead."},
        {"index": 2, "category": "Vehicle & Fuel",
         "what_it_was": "Diesel for the two service vans.",
         "why_category": "Recurring fleet card charge at a gas station → Vehicle & Fuel, automatically, no receipt chasing."},
        {"index": 3, "category": "Payroll",
         "what_it_was": "Bi-weekly wages plus employer taxes.",
         "why_category": "Split for you — gross pay to Payroll, the employer portion to Payroll Taxes, so your labor cost is clean."},
        {"index": 4, "category": "Service Revenue",
         "what_it_was": "Final balance on the Midland heat-pump replacement, paid outside the card system.",
         "why_category": "Matched to open Invoice #1042, so it counts as Service Revenue — not an untracked transfer."},
        {"index": 5, "category": "Bank Charges",
         "what_it_was": "Business checking account fee.",
         "why_category": "Bank's own fee → Bank Charges, kept separate from your real operating expenses."},
        {"index": 6, "category": "Supplies",
         "what_it_was": "Conduit, fittings, and a replacement drill.",
         "why_category": "Consumable job materials, not resold equipment → Supplies. The drill is under your $500 threshold, so it's expensed, not capitalized."},
        {"index": 7, "category": "Supplies",
         "what_it_was": "Line sets, refrigerant, and a contactor for two repair calls.",
         "why_category": "Job materials consumed on service work → Supplies."},
        {"index": 8, "category": "Operating Exp.",
         "what_it_was": "Monthly tech uniforms and shop mats.",
         "why_category": "Recurring vendor on a service contract → Operating Expense."},
        {"index": 9, "category": "Insurance",
         "what_it_was": "Monthly liability and commercial-auto premium.",
         "why_category": "Recurring insurer ACH → Insurance, not lumped into overhead."},
        {"index": 10, "category": "Service Revenue",
         "what_it_was": "Card payments for 6 completed jobs in the second weekly batch.",
         "why_category": "Core service revenue → Service Revenue."},
        {"index": 11, "category": "COGS — Equipment",
         "what_it_was": "Two-stage gas furnace for the Smiths Station changeout.",
         "why_category": "Equipment resold on a job → COGS — Equipment."},
        {"index": 12, "category": "Vehicle & Fuel",
         "what_it_was": "Diesel and DEF for the vans.",
         "why_category": "Fleet card at a fuel station → Vehicle & Fuel."},
        {"index": 13, "category": "Software",
         "what_it_was": "Your field-service management subscription.",
         "why_category": "Recurring SaaS charge → Software & Subscriptions."},
        {"index": 14, "category": "Service Revenue",
         "what_it_was": "Final weekly batch — 7 jobs including two maintenance-plan renewals.",
         "why_category": "Service Revenue, with the renewals tagged as recurring."},
        {"index": 15, "category": "Advertising",
         "what_it_was": "“AC repair Columbus GA” search campaign.",
         "why_category": "Recurring spend with an ad platform → Advertising & Marketing."},
        {"index": 16, "category": "Payroll",
         "what_it_was": "Second bi-weekly payroll of the month.",
         "why_category": "Wages to Payroll, employer taxes split out automatically."},
        {"index": 17, "category": "Owner's Draw",
         "what_it_was": "Owner moved profit to personal savings.",
         "why_category": "Not a business expense → Owner's Draw, so it doesn't reduce your reported profit."},
        {"index": 18, "category": "Loan Payment",
         "what_it_was": "Monthly note on the 2024 Transit service van.",
         "why_category": "Split into Loan Interest (expense) and Loan Principal (balance-sheet) — only the interest hits your P&L."},
    ],
    "what_changed": [
        "<b>Revenue was your best of the year</b> — up 11% on the spring AC-repair rush. Eight of those jobs came from the Google Ads campaign, which is now paying for itself roughly 19× over.",
        "<b>Margin widened to 20.8%</b> because revenue grew faster than payroll. You added one tech in March; this is the first full month they were billable rather than just a cost.",
        "<b>The books are caught up.</b> Last month you carried 47 uncategorized transactions. All 47 are now sorted, matched to invoices where possible, and explained above — nothing is sitting in “Ask My Accountant.”",
    ],
    "miscatches": [
        "An <b>$1,180 Carrier equipment</b> charge was auto-booked as <span class=\"from\">Supplies</span> → moved to <span class=\"fix\">COGS — Equipment</span>. Supplies were overstated; gross margin on that job is now correct.",
        "A <b>$2,400 owner transfer</b> to personal savings was sitting in <span class=\"from\">Expenses</span> → reclassed to <span class=\"fix\">Owner's Draw</span>. It's not a business cost and shouldn't reduce your profit.",
        "A <b>$540 duplicate</b> from a double-swiped Ferguson charge was flagged; the credit was matched, so it nets to <span class=\"fix\">$0</span> instead of inflating Supplies.",
    ],
    "one_thing_title": "Move your van loan payment off the credit card.",
    "one_thing_body": (
        "Your $720/mo service-van payment is running through the business card and getting auto-split "
        "between interest and principal each month — but the card charges <span class=\"dollar\">21.9% APR</span> "
        "on the carried balance. Paying it from checking instead would stop roughly "
        "<span class=\"dollar\">$1,420 a year</span> in avoidable interest. That's the single cleanup with real "
        "dollars attached this month."
    ),
    "watch_next": [
        "<b>The quarterly tax set-aside</b> is due June 15 — move it to a separate account this week so it's out of spending reach.",
        "<b>Two maintenance-plan renewals</b> recurred this month and four more are due in June; we'll track whether your renewal rate holds above 80%.",
        "<b>$4,700 of equipment</b> was bought ahead of June installs — watch that it converts to revenue and doesn't sit as idle inventory.",
        "<b>The March-hire tech</b> is now billable — track their job hours against payroll cost next month to confirm they're fully paying for themselves.",
    ],
}


def main():
    for tier in ("starter", "growth", "pro"):
        path = render_from_csv(CSV, tier=tier, prose=PROSE, is_sample=True)
        print(f"  {tier:<8} -> {path}")


if __name__ == "__main__":
    main()
