"""
EchoFrame reminder / safety-net job
─────────────────────────────────────────────────────────────────────────────
Runs on a daily Vercel Cron (see vercel.json). For every billing period that was
charged but whose files still haven't arrived after REMINDER_AFTER_DAYS (4):

  • re-send the secure upload link to the client, and
  • alert the owner (jacob.starling@echoframe.net) so they can chase it.

State lives in the durable store (Upstash Redis in prod, in-memory in dev). Each
period is reminded at most once — the `reminded` flag on the period record stops
the cron from nagging the same client every day.
"""

from __future__ import annotations

import os
import time
import traceback

import store
import sign
import emails
from registry import get_product

REMINDER_AFTER_DAYS = int(os.environ.get("REMINDER_AFTER_DAYS", "4"))


def _product_label(slug: str) -> str:
    prod = get_product(slug)
    return prod.label if prod else (slug or "report")


def run_reminders(*, _now: int | None = None) -> dict:
    """Scan pending periods and act on any that are overdue.

    Returns a summary dict (counts only — no PII) suitable for logging and for
    the cron endpoint's JSON response.
    """
    now = int(_now if _now is not None else time.time())
    cutoff = REMINDER_AFTER_DAYS * 24 * 3600
    base_url = os.environ.get("PUBLIC_BASE_URL", "")

    summary = {"checked": 0, "reminded": 0, "already": 0, "errors": 0}

    for safe_email, period in store.list_pending_periods():
        summary["checked"] += 1
        rec = store.load_period(safe_email, period)
        if not rec:
            continue

        # Already uploaded (race with an in-flight upload) — clear and skip.
        if rec.get("uploaded"):
            store.set_remove("ef:pending_periods", f"{safe_email}:{period}")
            continue

        # Only act once the grace window has elapsed.
        billed_at = int(rec.get("billed_at", 0))
        if now - billed_at < cutoff:
            continue

        # Already reminded — don't nag again.
        if rec.get("reminded"):
            summary["already"] += 1
            continue

        email   = rec.get("email", "")
        name    = rec.get("name", "") or "Client"
        product = rec.get("product", "")
        tier    = rec.get("tier", "")
        if not email or not product:
            continue

        try:
            token = sign.make_token(email, product, tier, period, _now=now)
            url   = sign.build_upload_url(base_url, email, product, tier, token)
            label = _product_label(product)
            days_overdue = (now - billed_at) // (24 * 3600)

            emails.send_reminder(email, name, label, url, period_label=period)
            emails.send_owner_alert(email, name, label, period, days_overdue)

            rec["reminded"] = True
            rec["reminded_at"] = now
            store.save_period(safe_email, period, rec)
            summary["reminded"] += 1
            print(f"[EchoFrame] Reminder sent (period={period}, product={product}).")  # no PII
        except Exception:
            summary["errors"] += 1
            print(f"[EchoFrame] REMINDER ERROR:\n{traceback.format_exc()}", flush=True)

    print(f"[EchoFrame] Reminder run complete: {summary}")
    return summary
