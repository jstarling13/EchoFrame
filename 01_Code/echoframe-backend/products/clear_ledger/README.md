# Clear Ledger

- **Engine:** `clear_ledger_engine.py`
- **Template:** `clear_ledger.html.j2`
- **Tiers:** starter, growth (one shared engine + template; tier is a runtime parameter)

## Documents the customer provides

Your file should include one row per open invoice, with:
- Customer name
- Invoice number
- Amount owed ($)
- Due date (or days overdue)
- Optional: total collected this month & average days-to-pay

**Where to export from:** QuickBooks, Xero, or FreshBooks can export an A/R aging or open-invoices report to CSV.
