"""
Rate Watch — offline demo.  Run:  python demo.py
Prints a vendor rate report for a sample small business. No external calls.
"""

from datetime import date, timedelta

import engine


def main() -> int:
    today = date.today()
    vendors = [
        engine.Vendor("FirstData Merchant", "merchant processing", 980.0,
                      renewal_date=today + timedelta(days=18)),
        engine.Vendor("Gusto", "payroll software", 75.0),
        engine.Vendor("QuickBooks Online", "accounting software", 90.0,
                      renewal_date=today + timedelta(days=200)),
        engine.Vendor("Comcast Business", "internet", 260.0,
                      renewal_date=today + timedelta(days=25)),
        engine.Vendor("Cintas", "linen / uniform", 210.0),
        engine.Vendor("LocalPest LLC", "pest control", 70.0),
        engine.Vendor("Mystery SaaS", "ai widgets", 300.0),  # no benchmark category
    ]

    report = engine.analyze_vendors(vendors, today=today)
    print(engine.render_report_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
