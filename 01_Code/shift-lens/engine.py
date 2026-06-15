"""
Shift Lens — per-shift labor-vs-revenue P&L engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from intelligence/strata.html):
  "Some shifts are paying for themselves. Others are quietly bleeding you out.
   Now you can tell which is which."
  1. Connect your POS and scheduling
  2. We map every shift (labor cost vs revenue)
  3. You get a weekly Shift Report  (shift-by-shift P&L, underperformer flags,
     schedule recommendations)

Pure Python, no external calls. The MVP ingests already-joined shift rows
(revenue + labor for each shift). In production the POS↔scheduling join happens
upstream; that integration is the documented seam — the P&L math here is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


DEFAULT_TARGET_LABOR_PCT = 30.0   # labor cost as % of revenue (restaurant default)


@dataclass
class Shift:
    label: str                         # e.g. "Mon Dinner"
    revenue: float
    # provide either labor_cost directly, or labor_hours + avg_wage
    labor_cost: Optional[float] = None
    labor_hours: Optional[float] = None
    avg_wage: Optional[float] = None

    def resolved_labor_cost(self) -> float:
        if self.labor_cost is not None:
            return float(self.labor_cost)
        if self.labor_hours is not None and self.avg_wage is not None:
            return float(self.labor_hours) * float(self.avg_wage)
        raise ValueError(
            f"Shift '{self.label}' needs labor_cost, or labor_hours + avg_wage."
        )


@dataclass
class ShiftResult:
    label: str
    revenue: float
    labor_cost: float
    labor_pct: Optional[float]         # None when revenue == 0
    contribution: float               # revenue - labor_cost
    status: str                       # "healthy" | "watch" | "underperforming" | "no_revenue"
    recommendation: str


def _classify(revenue: float, labor_cost: float, labor_pct: Optional[float],
              target_labor_pct: float) -> tuple[str, str]:
    if revenue <= 0:
        return ("no_revenue",
                "No revenue recorded for this shift. If it's scheduled, consider cutting it "
                "or merging it into an adjacent shift.")
    if labor_cost >= revenue:
        return ("underperforming",
                "Labor cost meets or exceeds revenue — this shift loses money. Cut it, shorten "
                "it, or cut one position and re-test next week.")
    if labor_pct is not None and labor_pct > target_labor_pct * 1.5:
        return ("underperforming",
                f"Labor is {labor_pct:.0f}% of revenue, well above the {target_labor_pct:.0f}% "
                f"target. Reduce headcount or hours on this shift.")
    if labor_pct is not None and labor_pct > target_labor_pct:
        return ("watch",
                f"Labor is {labor_pct:.0f}% of revenue, above the {target_labor_pct:.0f}% target. "
                f"Trim one position or tighten the schedule and watch next week.")
    return ("healthy",
            f"Labor is {labor_pct:.0f}% of revenue — at or under target. Keep this schedule.")


def analyze_shift(shift: Shift, *, target_labor_pct: float = DEFAULT_TARGET_LABOR_PCT) -> ShiftResult:
    revenue = float(shift.revenue)
    labor_cost = shift.resolved_labor_cost()
    labor_pct = round(labor_cost / revenue * 100, 1) if revenue > 0 else None
    contribution = round(revenue - labor_cost, 2)
    status, recommendation = _classify(revenue, labor_cost, labor_pct, target_labor_pct)
    return ShiftResult(
        label=shift.label, revenue=round(revenue, 2), labor_cost=round(labor_cost, 2),
        labor_pct=labor_pct, contribution=contribution,
        status=status, recommendation=recommendation,
    )


def analyze_week(shifts: list[Shift], *,
                 target_labor_pct: float = DEFAULT_TARGET_LABOR_PCT) -> dict:
    """Analyze a week of shifts and return a structured Shift Report dict."""
    results = [analyze_shift(s, target_labor_pct=target_labor_pct) for s in shifts]

    total_revenue = round(sum(r.revenue for r in results), 2)
    total_labor = round(sum(r.labor_cost for r in results), 2)
    overall_labor_pct = round(total_labor / total_revenue * 100, 1) if total_revenue > 0 else None
    total_contribution = round(total_revenue - total_labor, 2)

    underperformers = [r for r in results if r.status in ("underperforming", "no_revenue")]
    underperformers.sort(key=lambda r: r.contribution)   # worst (most negative) first

    ranked = sorted(results, key=lambda r: r.contribution, reverse=True)
    best = ranked[0] if ranked else None
    worst = ranked[-1] if ranked else None

    return {
        "target_labor_pct": target_labor_pct,
        "shift_count": len(results),
        "total_revenue": total_revenue,
        "total_labor": total_labor,
        "overall_labor_pct": overall_labor_pct,
        "total_contribution": total_contribution,
        "results": results,
        "underperformers": underperformers,
        "best_shift": best,
        "worst_shift": worst,
    }


def render_report_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("SHIFT LENS — WEEKLY SHIFT REPORT")
    lines.append("")
    olp = report["overall_labor_pct"]
    olp_str = f"{olp:.0f}%" if olp is not None else "n/a"
    lines.append(
        f"{report['shift_count']} shifts · revenue ${report['total_revenue']:,.0f} · "
        f"labor ${report['total_labor']:,.0f} ({olp_str} of revenue) · "
        f"contribution ${report['total_contribution']:,.0f}."
    )
    lines.append(f"Target labor: {report['target_labor_pct']:.0f}% of revenue.")
    lines.append("")

    lines.append("SHIFT-BY-SHIFT P&L:")
    for r in report["results"]:
        lp = f"{r.labor_pct:.0f}%" if r.labor_pct is not None else "n/a"
        lines.append(
            f"  [{r.status:>16}] {r.label}: rev ${r.revenue:,.0f}, labor ${r.labor_cost:,.0f} "
            f"({lp}), contribution ${r.contribution:,.0f}"
        )
    lines.append("")

    if report["underperformers"]:
        lines.append("UNDERPERFORMING SHIFTS (act on these):")
        for r in report["underperformers"]:
            lines.append(f"  • {r.label}: {r.recommendation}")
        lines.append("")
    else:
        lines.append("No underperforming shifts this week.")
        lines.append("")

    if report["best_shift"] and report["worst_shift"]:
        lines.append(
            f"Best: {report['best_shift'].label} "
            f"(${report['best_shift'].contribution:,.0f}). "
            f"Worst: {report['worst_shift'].label} "
            f"(${report['worst_shift'].contribution:,.0f})."
        )
    lines.append("")
    lines.append("Shift Lens is informational only — verify before changing any schedule.")
    return "\n".join(lines)
