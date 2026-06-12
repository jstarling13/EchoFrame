# Rate Watch

- **Engine:** `rate_watch_engine.py`
- **Template:** `rate_watch.html.j2`
- **Tiers:** core, pro (one shared engine + template; tier is a runtime parameter)

## Documents the customer provides

Your file should include one row per vendor or recurring bill, with:
- Vendor name
- Category (e.g. card processing, software, insurance)
- Current rate or contract amount ($)
- Billing basis (monthly, % of volume, per unit, etc.)
- Renewal or contract-end date

**Where to export from:** Pull these from your bills, statements, and vendor contracts into a simple spreadsheet, then export to CSV.
