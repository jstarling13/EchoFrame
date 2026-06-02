"""
Bay Coach — service-recommendation engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from ops/baysignal.html):
  "The right service recommendation at every write-up — based on what the vehicle
   actually needs, not what the advisor happened to remember."
  1. Connect your shop management system
  2. Recommendations surface at write-up (from vehicle history + mileage)
  3. The advisor presents, the customer decides

Pure Python, no external calls. Given a vehicle's current mileage and its service
history, a maintenance-interval rules table determines which services are due or
overdue and ranks them for the advisor. The shop-management-system integration is
the documented seam; the recommendation logic here is what it feeds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ServiceRule:
    name: str
    interval_miles: Optional[int] = None
    interval_months: Optional[int] = None
    # mileage past the interval (in miles) before it's "overdue" rather than just "due"
    overdue_grace_miles: int = 1000


# Standard maintenance interval table (typical passenger vehicle). Replace/extend
# per-make in production; the engine logic is unchanged.
DEFAULT_RULES: list[ServiceRule] = [
    ServiceRule("Oil & filter change", interval_miles=5000, interval_months=6),
    ServiceRule("Tire rotation", interval_miles=7500),
    ServiceRule("Engine air filter", interval_miles=15000),
    ServiceRule("Cabin air filter", interval_miles=15000, interval_months=12),
    ServiceRule("Brake inspection", interval_miles=15000, interval_months=12),
    ServiceRule("Brake fluid flush", interval_miles=30000, interval_months=36),
    ServiceRule("Coolant flush", interval_miles=30000, interval_months=60),
    ServiceRule("Transmission fluid", interval_miles=60000),
    ServiceRule("Spark plugs", interval_miles=60000),
    ServiceRule("Serpentine belt", interval_miles=90000),
]


@dataclass
class ServiceRecord:
    service: str          # should match a ServiceRule.name
    mileage: int
    performed_on: Optional[date] = None


@dataclass
class Vehicle:
    current_mileage: int
    history: list[ServiceRecord] = field(default_factory=list)
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    in_service_date: Optional[date] = None   # used for month-based intervals when no history


@dataclass
class Recommendation:
    service: str
    status: str                 # "overdue" | "due" | "upcoming" | "ok"
    reason: str
    miles_since_last: Optional[int]
    miles_until_due: Optional[int]
    last_mileage: Optional[int]
    priority: int               # higher = more urgent (for sorting)


def _last_record(history: list[ServiceRecord], service: str) -> Optional[ServiceRecord]:
    matches = [r for r in history if r.service.strip().lower() == service.strip().lower()]
    if not matches:
        return None
    return max(matches, key=lambda r: r.mileage)


def evaluate_rule(vehicle: Vehicle, rule: ServiceRule, *,
                  today: Optional[date] = None) -> Recommendation:
    today = today or date.today()
    last = _last_record(vehicle.history, rule.name)

    if rule.interval_miles is None:
        # Month-only rule: fall back to a simple due/ok by elapsed time if we can.
        return Recommendation(
            service=rule.name, status="ok",
            reason="No mileage interval defined; review manually.",
            miles_since_last=None, miles_until_due=None,
            last_mileage=last.mileage if last else None, priority=0,
        )

    if last is None:
        # Never recorded — assume due since the vehicle has accumulated mileage.
        miles_since = vehicle.current_mileage
        last_mileage = None
    else:
        miles_since = vehicle.current_mileage - last.mileage
        last_mileage = last.mileage

    miles_until_due = rule.interval_miles - miles_since

    if miles_since >= rule.interval_miles + rule.overdue_grace_miles:
        status, priority = "overdue", 3
        reason = (f"{miles_since:,} mi since last {rule.name.lower()} "
                  f"(interval {rule.interval_miles:,} mi) — overdue.")
    elif miles_since >= rule.interval_miles:
        status, priority = "due", 2
        reason = (f"{miles_since:,} mi since last {rule.name.lower()} "
                  f"(interval {rule.interval_miles:,} mi) — due now.")
    elif miles_until_due <= rule.interval_miles * 0.15:
        status, priority = "upcoming", 1
        reason = (f"Due in about {miles_until_due:,} mi — mention it so the customer can plan.")
    else:
        status, priority = "ok", 0
        reason = f"Not due for ~{miles_until_due:,} mi."

    # never-recorded items get a small bump so the advisor at least asks
    if last is None and status in ("due", "overdue"):
        reason += " No record on file for this vehicle — confirm with the customer."

    return Recommendation(
        service=rule.name, status=status, reason=reason,
        miles_since_last=miles_since, miles_until_due=miles_until_due,
        last_mileage=last_mileage, priority=priority,
    )


def recommend(vehicle: Vehicle, *, rules: Optional[list[ServiceRule]] = None,
              today: Optional[date] = None) -> dict:
    """Return ranked service recommendations for a vehicle at write-up."""
    rules = rules or DEFAULT_RULES
    recs = [evaluate_rule(vehicle, r, today=today) for r in rules]

    # Rank: most urgent first, then by miles overdue (most negative miles_until_due first)
    recs.sort(key=lambda r: (-r.priority,
                             r.miles_until_due if r.miles_until_due is not None else 0))

    actionable = [r for r in recs if r.status in ("overdue", "due", "upcoming")]
    return {
        "vehicle": {
            "year": vehicle.year, "make": vehicle.make, "model": vehicle.model,
            "current_mileage": vehicle.current_mileage,
        },
        "recommendations": recs,
        "actionable": actionable,
        "overdue_count": sum(1 for r in recs if r.status == "overdue"),
        "due_count": sum(1 for r in recs if r.status == "due"),
    }


def render_writeup_text(result: dict) -> str:
    v = result["vehicle"]
    desc = " ".join(str(x) for x in (v["year"], v["make"], v["model"]) if x) or "Vehicle"
    lines: list[str] = []
    lines.append("BAY COACH — RECOMMENDED AT WRITE-UP")
    lines.append(f"{desc} · {v['current_mileage']:,} mi")
    lines.append("")
    if not result["actionable"]:
        lines.append("Nothing due right now. Vehicle is up to date on tracked services.")
        return "\n".join(lines)
    for r in result["actionable"]:
        lines.append(f"  [{r.status.upper():>8}] {r.service} — {r.reason}")
    lines.append("")
    lines.append("Advisor presents; customer decides. Recommendations are based on mileage and "
                 "service history, not a physical inspection.")
    return "\n".join(lines)
