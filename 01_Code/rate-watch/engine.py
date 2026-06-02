"""
Rate Watch — vendor rate benchmarking engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from intelligence/oryn.html):
  "Every vendor you pay has a market rate. Find out how many of yours are above it."
  1. Enter your vendors and what you pay
  2. We benchmark against the local market
  3. You get a report with the gaps  (+ renewal alerts 30 days out)

This module is pure Python (no external calls). It compares each vendor's monthly
spend against a curated market-rate band for its category, computes the overpayment,
ranks the gaps, and surfaces renewals due within a configurable window.

The market-rate bands here are a curated sample table (the same approach the flagship
Clarity Report uses for industry benchmarks). In production this is replaced by a
real local-market data feed; the comparison logic does not change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ── Sample market-rate bands (monthly $), keyed by vendor category ─────────────
# (low, typical, high) for a small business. Replace with a live feed in production.
MARKET_RATES: dict[str, tuple[float, float, float]] = {
    "merchant processing":   (200.0, 450.0, 900.0),
    "payroll software":      (40.0, 80.0, 160.0),
    "accounting software":   (30.0, 70.0, 150.0),
    "pos system":            (60.0, 120.0, 250.0),
    "internet":              (80.0, 150.0, 300.0),
    "phone / voip":          (30.0, 75.0, 160.0),
    "insurance (liability)": (150.0, 350.0, 700.0),
    "waste / sanitation":    (120.0, 250.0, 500.0),
    "linen / uniform":       (90.0, 200.0, 400.0),
    "pest control":          (40.0, 90.0, 180.0),
    "security / alarm":      (40.0, 80.0, 160.0),
    "software / saas":       (20.0, 60.0, 200.0),
    "cleaning service":      (200.0, 450.0, 900.0),
    "marketing agency":      (500.0, 1500.0, 4000.0),
    "equipment lease":       (150.0, 400.0, 1000.0),
}

DEFAULT_RENEWAL_WINDOW_DAYS = 30


@dataclass
class Vendor:
    name: str
    category: str
    monthly_cost: float
    renewal_date: Optional[date] = None  # next contract renewal, if known


@dataclass
class VendorFinding:
    name: str
    category: str
    monthly_cost: float
    market_typical: Optional[float]
    market_high: Optional[float]
    # positive overpay = paying above the typical market rate
    overpay_monthly: Optional[float]
    overpay_pct: Optional[float]
    status: str                      # "over" | "within" | "under" | "no_benchmark"
    renewal_date: Optional[date] = None
    days_to_renewal: Optional[int] = None
    renewal_soon: bool = False


def _normalize_category(category: str) -> str:
    return (category or "").strip().lower()


def analyze_vendor(vendor: Vendor, *, today: Optional[date] = None,
                   renewal_window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS) -> VendorFinding:
    """Benchmark a single vendor against its category's market band."""
    today = today or date.today()
    cat = _normalize_category(vendor.category)
    band = MARKET_RATES.get(cat)

    days_to_renewal = None
    renewal_soon = False
    if vendor.renewal_date is not None:
        days_to_renewal = (vendor.renewal_date - today).days
        renewal_soon = 0 <= days_to_renewal <= renewal_window_days

    if band is None:
        return VendorFinding(
            name=vendor.name, category=vendor.category,
            monthly_cost=vendor.monthly_cost,
            market_typical=None, market_high=None,
            overpay_monthly=None, overpay_pct=None,
            status="no_benchmark",
            renewal_date=vendor.renewal_date,
            days_to_renewal=days_to_renewal, renewal_soon=renewal_soon,
        )

    low, typical, high = band
    overpay_monthly = round(vendor.monthly_cost - typical, 2)
    overpay_pct = round((vendor.monthly_cost - typical) / typical * 100, 1) if typical else None

    if vendor.monthly_cost > high:
        status = "over"
    elif vendor.monthly_cost > typical:
        status = "over"
    elif vendor.monthly_cost < low:
        status = "under"
    else:
        status = "within"

    return VendorFinding(
        name=vendor.name, category=vendor.category,
        monthly_cost=vendor.monthly_cost,
        market_typical=typical, market_high=high,
        overpay_monthly=overpay_monthly, overpay_pct=overpay_pct,
        status=status,
        renewal_date=vendor.renewal_date,
        days_to_renewal=days_to_renewal, renewal_soon=renewal_soon,
    )


def analyze_vendors(vendors: list[Vendor], *, today: Optional[date] = None,
                    renewal_window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS) -> dict:
    """Analyze a list of vendors and return a structured report dict."""
    findings = [
        analyze_vendor(v, today=today, renewal_window_days=renewal_window_days)
        for v in vendors
    ]

    # Rank overpayers by monthly dollars saved (largest first)
    overpayers = sorted(
        (f for f in findings if f.status == "over" and (f.overpay_monthly or 0) > 0),
        key=lambda f: f.overpay_monthly or 0, reverse=True,
    )
    total_monthly_overpay = round(sum(f.overpay_monthly or 0 for f in overpayers), 2)

    renewals_due = sorted(
        (f for f in findings if f.renewal_soon),
        key=lambda f: f.days_to_renewal if f.days_to_renewal is not None else 9999,
    )

    return {
        "generated": (today or date.today()).isoformat(),
        "vendor_count": len(findings),
        "overpayer_count": len(overpayers),
        "total_monthly_overpay": total_monthly_overpay,
        "total_annual_overpay": round(total_monthly_overpay * 12, 2),
        "findings": findings,
        "overpayers": overpayers,
        "renewals_due": renewals_due,
    }


def render_report_text(report: dict) -> str:
    """Plain-text summary of an analysis report (the 'report with the gaps')."""
    lines: list[str] = []
    lines.append("RATE WATCH — VENDOR RATE REPORT")
    lines.append(f"Generated: {report['generated']}")
    lines.append("")
    lines.append(
        f"Reviewed {report['vendor_count']} vendors. "
        f"{report['overpayer_count']} are above the typical market rate."
    )
    if report["total_monthly_overpay"] > 0:
        lines.append(
            f"Estimated overpayment: ${report['total_monthly_overpay']:,.0f}/mo "
            f"(${report['total_annual_overpay']:,.0f}/yr) if every gap is closed to the typical rate."
        )
    lines.append("")

    if report["overpayers"]:
        lines.append("TOP OVERPAYMENTS (largest monthly gap first):")
        for f in report["overpayers"]:
            lines.append(
                f"  • {f.name} ({f.category}): paying ${f.monthly_cost:,.0f}/mo vs "
                f"${f.market_typical:,.0f} typical — ${f.overpay_monthly:,.0f}/mo "
                f"({f.overpay_pct:+.0f}%) above market."
            )
        lines.append("")
    else:
        lines.append("No vendors above market rate. Nice.")
        lines.append("")

    if report["renewals_due"]:
        lines.append("RENEWALS DUE SOON (renegotiate before these dates):")
        for f in report["renewals_due"]:
            lines.append(
                f"  • {f.name} ({f.category}): renews {f.renewal_date.isoformat()} "
                f"in {f.days_to_renewal} days."
            )
        lines.append("")

    lines.append(
        "Note: market rates are sample benchmark bands, not a quote. "
        "Rate Watch is informational only — verify with each vendor before renegotiating."
    )
    return "\n".join(lines)


def parse_renewal_date(value) -> Optional[date]:
    """Accept date, ISO string, or None."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
