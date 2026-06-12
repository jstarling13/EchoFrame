# Auto Ledger

- **Engine:** `auto_ledger_engine.py`
- **Template:** `auto_ledger.html.j2`
- **Tiers:** starter, growth, pro (one shared engine + template; tier is a runtime parameter)

## Documents the customer provides

Your file should include one row per transaction, with:
- Date of each transaction
- Description / payee
- Amount - signed (deposits positive, expenses negative)
- Account it came from (checking, card, etc.)
- Optional: your accounting revenue & net-income totals for the month

**Where to export from:** Your bank and credit-card sites export transactions to CSV; most accounting tools do too.
