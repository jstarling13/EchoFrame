"""
EchoFrame product registry
─────────────────────────────────────────────────────────────────────────────
Single source of truth for every report product the upload endpoint can run.

Adding a new product is one entry:
  1. Build  <product>_engine.py  with  generate_<product>_report(email, name, ...).
  2. Add a thin adapter here that maps the generic (email, name, fields) call to it.
  3. Register it in PRODUCTS.

main.py imports nothing product-specific — it just routes by slug through this
registry, so the 12 remaining products plug in without touching the web layer.
"""

from dataclasses import dataclass, field
from typing import Callable

from engine import generate_clarity_report
from auto_ledger_engine import generate_auto_ledger_report
from rate_watch_engine import generate_rate_watch_report
from rival_scan_engine import generate_rival_scan_report
from shift_lens_engine import generate_shift_lens_report
from call_catch_engine import generate_call_catch_report
from quote_revive_engine import generate_quote_revive_report
from clear_ledger_engine import generate_clear_ledger_report
from revenue_suite_engine import generate_revenue_suite_report
from call_router_engine import generate_call_router_report
from permit_watch_engine import generate_permit_watch_report
from crew_hire_engine import generate_crew_hire_report
from bay_coach_engine import generate_bay_coach_report
from drive_pay_engine import generate_drive_pay_report


@dataclass(frozen=True)
class Product:
    slug: str
    label: str
    generate: Callable[[str, str, dict], str]   # (email, name, fields) -> report path
    tiers: tuple = ()                            # () = no tiers; else allowed tier slugs
    default_tier: str = ""

    def resolve_tier(self, tier: str) -> str:
        """Return a valid tier for this product, falling back to the default/first."""
        if not self.tiers:
            return ""
        tier = (tier or "").strip().lower()
        if tier in self.tiers:
            return tier
        return self.default_tier or self.tiers[0]


# ── Adapters: map the generic (email, name, fields) call onto each engine ───────

def _run_clarity(email: str, name: str, fields: dict) -> str:
    return generate_clarity_report(
        email, name,
        fields.get("industry", ""),
        fields.get("location", ""),
    )


def _run_auto_ledger(email: str, name: str, fields: dict) -> str:
    return generate_auto_ledger_report(
        email, name,
        tier=fields.get("tier", "starter"),
    )


def _run_rate_watch(email: str, name: str, fields: dict) -> str:
    return generate_rate_watch_report(
        email, name,
        tier=fields.get("tier", "core"),
    )


def _run_rival_scan(email: str, name: str, fields: dict) -> str:
    return generate_rival_scan_report(email, name)


def _run_shift_lens(email: str, name: str, fields: dict) -> str:
    return generate_shift_lens_report(email, name)


def _run_call_catch(email: str, name: str, fields: dict) -> str:
    return generate_call_catch_report(email, name)


def _run_quote_revive(email: str, name: str, fields: dict) -> str:
    return generate_quote_revive_report(email, name)


def _run_clear_ledger(email: str, name: str, fields: dict) -> str:
    return generate_clear_ledger_report(email, name, tier=fields.get("tier", "starter"))


def _run_revenue_suite(email: str, name: str, fields: dict) -> str:
    # Reads three per-product CSVs: <email>_callcatch.csv / _quoterevive.csv / _clearledger.csv
    return generate_revenue_suite_report(email, name)


def _run_call_router(email: str, name: str, fields: dict) -> str:
    return generate_call_router_report(email, name)


def _run_permit_watch(email: str, name: str, fields: dict) -> str:
    return generate_permit_watch_report(email, name)


def _run_crew_hire(email: str, name: str, fields: dict) -> str:
    return generate_crew_hire_report(email, name)


def _run_bay_coach(email: str, name: str, fields: dict) -> str:
    return generate_bay_coach_report(email, name)


def _run_drive_pay(email: str, name: str, fields: dict) -> str:
    return generate_drive_pay_report(email, name)


# ── Registry ────────────────────────────────────────────────────────────────────

PRODUCTS: dict[str, Product] = {
    "clarity": Product(
        slug="clarity",
        label="Monthly Clarity Report",
        generate=_run_clarity,
    ),
    "auto-ledger": Product(
        slug="auto-ledger",
        label="Auto Ledger",
        generate=_run_auto_ledger,
        tiers=("starter", "growth", "pro"),
        default_tier="starter",
    ),
    "rate-watch": Product(
        slug="rate-watch",
        label="Rate Watch",
        generate=_run_rate_watch,
        tiers=("core", "pro"),
        default_tier="core",
    ),
    "rival-scan": Product(
        slug="rival-scan",
        label="Rival Scan",
        generate=_run_rival_scan,
    ),
    "shift-lens": Product(
        slug="shift-lens",
        label="Shift Lens",
        generate=_run_shift_lens,
    ),
    "call-catch": Product(
        slug="call-catch",
        label="Call Catch",
        generate=_run_call_catch,
    ),
    "quote-revive": Product(
        slug="quote-revive",
        label="Quote Revive",
        generate=_run_quote_revive,
    ),
    "clear-ledger": Product(
        slug="clear-ledger",
        label="Clear Ledger",
        generate=_run_clear_ledger,
        tiers=("starter", "growth"),
        default_tier="starter",
    ),
    "revenue-suite": Product(
        slug="revenue-suite",
        label="Revenue Suite",
        generate=_run_revenue_suite,
    ),
    "call-router": Product(
        slug="call-router",
        label="Call Router",
        generate=_run_call_router,
    ),
    "permit-watch": Product(
        slug="permit-watch",
        label="Permit Watch",
        generate=_run_permit_watch,
    ),
    "crew-hire": Product(
        slug="crew-hire",
        label="Crew Hire",
        generate=_run_crew_hire,
    ),
    "bay-coach": Product(
        slug="bay-coach",
        label="Bay Coach",
        generate=_run_bay_coach,
    ),
    "drive-pay": Product(
        slug="drive-pay",
        label="Drive Pay",
        generate=_run_drive_pay,
    ),
    # All 13 product report-generators registered. Remaining future products register here.
}


def get_product(slug: str) -> Product:
    """Look up a product by slug; default to the flagship Clarity Report."""
    return PRODUCTS.get((slug or "").strip().lower(), PRODUCTS["clarity"])


# ── Stripe product → report routing ─────────────────────────────────────────────
# Maps the LIVE Stripe product IDs (account acct_1Ta0p0RoVBvZMFsw "EchoFrame",
# pulled 2026-06-07) to (report slug, tier). Tier is "" for single-tier products.
# Two Stripe products intentionally map to None — no report engine exists for them
# yet, so a purchase of those must be flagged, never silently mis-routed.
STRIPE_PRODUCT_MAP: dict[str, tuple] = {
    "prod_Ue1bNa1QnMWtAH": ("auto-ledger", "starter"),   # Auto Ledger — Starter
    "prod_Ue1cVan2GYZL9L": ("auto-ledger", "growth"),    # Auto Ledger — Growth
    "prod_Ue1ct7Bd1RQWBE": ("auto-ledger", "pro"),       # Auto Ledger — Pro
    "prod_Ue1lOcCbCsCoPq": ("rate-watch", "core"),       # Rate Watch — Core
    "prod_Ue1m1nEwjMTOBK": ("rate-watch", "pro"),        # Rate Watch — Pro
    "prod_Ue20HGc7c6jtrr": ("rival-scan", ""),           # Rival Scan
    "prod_Ue23nnsQ9nQaqQ": ("shift-lens", ""),           # Shift Lens
    "prod_Ue3LCWjYEwGqWW": ("call-catch", ""),           # Call Catch
    "prod_Ue3NrpJ8SclPJx": ("quote-revive", ""),         # Quote Revive
    "prod_Ue3PvcZyR8a7lr": ("clear-ledger", "starter"),  # Clear Ledger — Starter
    "prod_Ue3QcydJBgWDyl": ("clear-ledger", "growth"),   # Clear Ledger — Growth
    "prod_Ue3SpOhz5wzWLQ": ("call-router", ""),          # Call Router
    "prod_Ue3UzBvqRIX5UQ": ("permit-watch", ""),         # Permit Watch
    "prod_Ue3Wup8RVJjPyO": ("crew-hire", ""),            # Crew Hire
    "prod_Ue3YS5dFzFFVa3": ("bay-coach", ""),            # Bay Coach
    "prod_Ue3b9nr0TWUXKP": ("drive-pay", ""),            # Drive Pay
    "prod_UZ9RW25uUul5eB": ("clarity", ""),              # Monthly Clarity Report
    # ── No report engine yet — flag on purchase, do NOT mis-route ──
    "prod_UZ9ThERnLPNfVL": None,                          # Competitor & Market Landscape Report
    "prod_UZ9Sm7JPLrLy9x": None,                          # EchoFrame Business Audit
}

# Fallback name-based routing (when only a product/plan NAME is available, not the ID).
# Matched case-insensitively as a substring; tier inferred from the suffix.
_NAME_ROUTES = (
    ("auto ledger", "auto-ledger"), ("rate watch", "rate-watch"),
    ("rival scan", "rival-scan"), ("shift lens", "shift-lens"),
    ("call catch", "call-catch"), ("quote revive", "quote-revive"),
    ("clear ledger", "clear-ledger"), ("call router", "call-router"),
    ("permit watch", "permit-watch"), ("crew hire", "crew-hire"),
    ("bay coach", "bay-coach"), ("drive pay", "drive-pay"),
    ("revenue suite", "revenue-suite"), ("clarity", "clarity"),
)
_TIER_WORDS = ("starter", "growth", "pro", "core")


def route_stripe_purchase(product_id: str = "", product_name: str = "") -> dict:
    """Resolve a Stripe purchase to a report.

    Returns {"slug", "tier", "product": Product|None, "matched_by", "flag"}.
    NEVER guesses: an unknown/unmapped product returns product=None with a flag
    so the caller can surface it instead of generating the wrong report.
    """
    pid = (product_id or "").strip()
    if pid in STRIPE_PRODUCT_MAP:
        mapped = STRIPE_PRODUCT_MAP[pid]
        if mapped is None:
            return {"slug": "", "tier": "", "product": None, "matched_by": "id",
                    "flag": f"Stripe product {pid} has no report engine — needs review."}
        slug, tier = mapped
        return {"slug": slug, "tier": tier, "product": PRODUCTS.get(slug),
                "matched_by": "id", "flag": ""}

    name = (product_name or "").strip().lower()
    for needle, slug in _NAME_ROUTES:
        if needle in name:
            tier = next((w for w in _TIER_WORDS if w in name), "")
            prod = PRODUCTS.get(slug)
            return {"slug": slug, "tier": prod.resolve_tier(tier) if prod else tier,
                    "product": prod, "matched_by": "name", "flag": ""}

    return {"slug": "", "tier": "", "product": None, "matched_by": "none",
            "flag": f"Could not route Stripe purchase (id={product_id!r}, name={product_name!r}) "
                    f"to any report — flagged for review."}
