"""
Clear Ledger — invoice dunning + AR aging engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from revenue/clearledger.html):
  "You did the work. Clear Ledger makes sure you actually get paid for it — without
   you having to ask twice."
  1. Connect your invoicing tool
  2. Overdue invoices enter the follow-up sequence
  3. You only step in when it escalates  (structured follow-up, AR dashboard,
     relationship-preserving messaging, human handoff alerts)

Pure Python. The message sender is INJECTED (mock recorder by default), so no real
messages are sent here. The invoicing-tool integration is the documented seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional


# Days PAST DUE at which each dunning message fires (absolute milestones).
DEFAULT_DUNNING_DAYS = [1, 7, 14, 30]


@dataclass
class Invoice:
    invoice_id: str
    customer_name: str
    amount: float
    due_date: date
    status: str = "open"                 # open | paid
    reminders_sent: int = 0


@dataclass
class DunningAction:
    invoice_id: str
    customer_name: str
    step: int
    kind: str                            # "reminder" | "handoff"
    message: str
    days_overdue: int


Sender = Callable[[str, str], bool]


def _mock_sender_factory():
    sent: list[dict] = []

    def sender(recipient: str, message: str) -> bool:
        sent.append({"to": recipient, "message": message})
        return True

    sender.sent = sent  # type: ignore[attr-defined]
    return sender


def _compose_message(inv: Invoice, step: int, total_steps: int, days_overdue: int) -> str:
    name = inv.customer_name.split()[0] if inv.customer_name else "there"
    amt = f"${inv.amount:,.0f}"
    inv_ref = inv.invoice_id
    if step == 1:
        return (f"Hi {name}, a friendly reminder that invoice {inv_ref} for {amt} is now due. "
                f"If you've already sent it, thank you — please disregard.")
    if step < total_steps:
        return (f"Hi {name}, invoice {inv_ref} ({amt}) is {days_overdue} days past due. "
                f"Could you let me know when we can expect payment? Happy to send the link again.")
    return (f"Hi {name}, invoice {inv_ref} for {amt} is {days_overdue} days overdue. "
            f"This is a final notice before we follow up directly — please arrange payment or "
            f"reply so we can sort it out.")


def aging_bucket(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "current"
    if days_overdue <= 30:
        return "1-30"
    if days_overdue <= 60:
        return "31-60"
    return "60+"


def next_action(inv: Invoice, *, today: Optional[date] = None,
                schedule: Optional[list[int]] = None) -> Optional[DunningAction]:
    today = today or date.today()
    schedule = schedule or DEFAULT_DUNNING_DAYS

    if inv.status != "open":
        return None

    days_overdue = (today - inv.due_date).days
    if days_overdue < schedule[0]:
        return None

    if inv.reminders_sent >= len(schedule):
        if days_overdue >= schedule[-1]:
            return DunningAction(
                invoice_id=inv.invoice_id, customer_name=inv.customer_name,
                step=inv.reminders_sent + 1, kind="handoff",
                message=(f"Invoice {inv.invoice_id} ({inv.customer_name}) for "
                         f"${inv.amount:,.0f} is {days_overdue} days overdue after "
                         f"{inv.reminders_sent} reminders. Recommend a direct call."),
                days_overdue=days_overdue,
            )
        return None

    milestone = schedule[inv.reminders_sent]
    if days_overdue >= milestone:
        step = inv.reminders_sent + 1
        return DunningAction(
            invoice_id=inv.invoice_id, customer_name=inv.customer_name,
            step=step, kind="reminder",
            message=_compose_message(inv, step, len(schedule), days_overdue),
            days_overdue=days_overdue,
        )
    return None


def ar_summary(invoices: list[Invoice], *, today: Optional[date] = None) -> dict:
    """Accounts-receivable aging summary over the open invoices."""
    today = today or date.today()
    buckets = {"current": 0.0, "1-30": 0.0, "31-60": 0.0, "60+": 0.0}
    open_count = 0
    total_open = 0.0
    for inv in invoices:
        if inv.status != "open":
            continue
        open_count += 1
        total_open += inv.amount
        days_overdue = (today - inv.due_date).days
        buckets[aging_bucket(days_overdue)] += inv.amount
    return {
        "open_invoice_count": open_count,
        "total_outstanding": round(total_open, 2),
        "aging": {k: round(v, 2) for k, v in buckets.items()},
    }


def run_cycle(invoices: list[Invoice], *, today: Optional[date] = None,
              schedule: Optional[list[int]] = None,
              sender: Optional[Sender] = None) -> dict:
    """Send due reminders, escalate handoffs, and produce an AR summary."""
    today = today or date.today()
    schedule = schedule or DEFAULT_DUNNING_DAYS
    sender = sender or _mock_sender_factory()

    sent_actions: list[DunningAction] = []
    handoffs: list[DunningAction] = []

    for inv in invoices:
        action = next_action(inv, today=today, schedule=schedule)
        if action is None:
            continue
        if action.kind == "handoff":
            handoffs.append(action)
            continue
        if sender(inv.customer_name, action.message):
            inv.reminders_sent += 1
            sent_actions.append(action)

    return {
        "date": today.isoformat(),
        "invoices_processed": len(invoices),
        "reminders_sent": len(sent_actions),
        "handoffs": handoffs,
        "actions": sent_actions,
        "ar_summary": ar_summary(invoices, today=today),
        "sender": sender,
    }
