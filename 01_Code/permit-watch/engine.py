"""
Permit Watch — compliance expiry tracking engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from ops/permitwatch.html):
  "Every license, registration, and permit on one dashboard — with a heads-up
   30 days before anything expires."
  1. Enter your fleet and licenses
  2. Everything lands on one dashboard
  3. Alerts hit your inbox 30 days out  (+ per-vehicle tracking, document history)

Pure Python, no external calls. Tracks compliance items with expiry dates, computes
days-to-expiry and a status, groups by entity (e.g. a vehicle), and produces the
30-day alert digest the page promises.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# Alert windows (days). Configurable per call.
DEFAULT_ALERT_WINDOW_DAYS = 30
CRITICAL_WINDOW_DAYS = 7


@dataclass
class ComplianceItem:
    name: str                          # e.g. "Vehicle registration"
    category: str                      # registration | license | permit | insurance | inspection
    expiry_date: date
    entity: Optional[str] = None       # e.g. "Van 12" / "Truck 3" / business-wide if None
    identifier: Optional[str] = None   # plate, license #, policy #
    notes: Optional[str] = None


@dataclass
class ItemStatus:
    name: str
    category: str
    entity: Optional[str]
    identifier: Optional[str]
    expiry_date: date
    days_to_expiry: int
    status: str                        # "expired" | "critical" | "due_soon" | "upcoming" | "ok"
    alert: bool                        # within the alert window (and not yet expired-ignored)


def _status_for(days: int, alert_window: int) -> tuple[str, bool]:
    if days < 0:
        return ("expired", True)
    if days <= CRITICAL_WINDOW_DAYS:
        return ("critical", True)
    if days <= alert_window:
        return ("due_soon", True)
    if days <= alert_window * 2:
        return ("upcoming", False)
    return ("ok", False)


def evaluate_item(item: ComplianceItem, *, today: Optional[date] = None,
                  alert_window: int = DEFAULT_ALERT_WINDOW_DAYS) -> ItemStatus:
    today = today or date.today()
    days = (item.expiry_date - today).days
    status, alert = _status_for(days, alert_window)
    return ItemStatus(
        name=item.name, category=item.category, entity=item.entity,
        identifier=item.identifier, expiry_date=item.expiry_date,
        days_to_expiry=days, status=status, alert=alert,
    )


_STATUS_ORDER = {"expired": 0, "critical": 1, "due_soon": 2, "upcoming": 3, "ok": 4}


def build_dashboard(items: list[ComplianceItem], *, today: Optional[date] = None,
                    alert_window: int = DEFAULT_ALERT_WINDOW_DAYS) -> dict:
    """Evaluate all items and return a dashboard dict (the 'one dashboard')."""
    today = today or date.today()
    statuses = [evaluate_item(i, today=today, alert_window=alert_window) for i in items]

    # Sort: most urgent first (expired/critical), then by soonest expiry.
    statuses.sort(key=lambda s: (_STATUS_ORDER[s.status], s.days_to_expiry))

    alerts = [s for s in statuses if s.alert]
    expired = [s for s in statuses if s.status == "expired"]

    # Group by entity for per-vehicle tracking
    by_entity: dict[str, list[ItemStatus]] = {}
    for s in statuses:
        key = s.entity or "Business-wide"
        by_entity.setdefault(key, []).append(s)

    counts = {k: 0 for k in _STATUS_ORDER}
    for s in statuses:
        counts[s.status] += 1

    return {
        "generated": today.isoformat(),
        "alert_window_days": alert_window,
        "item_count": len(statuses),
        "counts": counts,
        "items": statuses,
        "alerts": alerts,
        "expired": expired,
        "by_entity": by_entity,
    }


def render_alert_digest(dashboard: dict) -> str:
    """The '30 days out' email digest — only items needing attention."""
    lines: list[str] = []
    lines.append("PERMIT WATCH — COMPLIANCE ALERTS")
    lines.append(f"As of {dashboard['generated']} "
                 f"(alerting {dashboard['alert_window_days']} days out)")
    lines.append("")

    if not dashboard["alerts"]:
        lines.append("Nothing expiring soon. All tracked items are current.")
        return "\n".join(lines)

    if dashboard["expired"]:
        lines.append("!! EXPIRED — fix immediately:")
        for s in dashboard["expired"]:
            who = f"{s.entity} · " if s.entity else ""
            lines.append(f"  • {who}{s.name} expired {abs(s.days_to_expiry)} days ago "
                         f"({s.expiry_date.isoformat()}).")
        lines.append("")

    soon = [s for s in dashboard["alerts"] if s.status in ("critical", "due_soon")]
    if soon:
        lines.append("EXPIRING SOON:")
        for s in soon:
            who = f"{s.entity} · " if s.entity else ""
            tag = "CRITICAL" if s.status == "critical" else "due"
            lines.append(f"  • [{tag}] {who}{s.name}: {s.days_to_expiry} days "
                         f"({s.expiry_date.isoformat()}).")
        lines.append("")

    lines.append("Renew these before their dates to stay compliant.")
    return "\n".join(lines)


def parse_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
