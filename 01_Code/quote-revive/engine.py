"""
Quote Revive — ghosted-quote follow-up engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from revenue/quoterevive.html):
  "You already did the work of quoting it. Quote Revive makes sure it actually closes."
  1. Connect your quoting or CRM tool
  2. Quote Revive spots the ones going cold
  3. You get the response, not the reminder  (timed follow-up sequences, quote
     status tracking, context-aware messaging, cold-lead reactivation)

Pure Python. The SMS/email sender is INJECTED and defaults to a mock recorder, so
no real messages are sent here. The quoting-tool/CRM integration is the documented
seam; the "spot the cold ones + run the sequence" logic is what this provides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional


# Days SINCE THE QUOTE WAS SENT at which each follow-up fires (absolute milestones).
# Index = follow-ups already sent. After the last milestone, the quote is escalated.
DEFAULT_SCHEDULE_DAYS = [2, 4, 7, 14]


@dataclass
class Quote:
    quote_id: str
    customer_name: str
    amount: float
    sent_date: date
    status: str = "open"                 # open | accepted | declined
    followups_sent: int = 0
    last_contact_date: Optional[date] = None   # defaults to sent_date if None

    def effective_last_contact(self) -> date:
        return self.last_contact_date or self.sent_date


@dataclass
class FollowUpAction:
    quote_id: str
    customer_name: str
    step: int                            # 1-based follow-up number being sent now
    kind: str                            # "followup" | "handoff"
    message: str
    days_since_contact: int


# A sender takes (recipient_name, message) and returns True on success.
Sender = Callable[[str, str], bool]


def _mock_sender_factory():
    sent: list[dict] = []

    def sender(recipient: str, message: str) -> bool:
        sent.append({"to": recipient, "message": message})
        return True

    sender.sent = sent  # type: ignore[attr-defined]
    return sender


def _compose_message(quote: Quote, step: int, total_steps: int) -> str:
    name = quote.customer_name.split()[0] if quote.customer_name else "there"
    amt = f"${quote.amount:,.0f}"
    if step == 1:
        return (f"Hi {name}, following up on the {amt} quote we sent. "
                f"Any questions I can answer to help you decide?")
    if step < total_steps:
        return (f"Hi {name}, just checking back on your {amt} quote. "
                f"Happy to adjust scope or timing if that helps.")
    return (f"Hi {name}, last note on the {amt} quote — if now isn't the right time, "
            f"no problem. Want me to hold it or close it out?")


def next_action(quote: Quote, *, today: Optional[date] = None,
                schedule: Optional[list[int]] = None) -> Optional[FollowUpAction]:
    """Return the follow-up (or handoff) due for this quote today, or None."""
    today = today or date.today()
    schedule = schedule or DEFAULT_SCHEDULE_DAYS

    if quote.status != "open":
        return None

    days_since_sent = (today - quote.sent_date).days

    # All scheduled follow-ups exhausted → escalate to human handoff once.
    if quote.followups_sent >= len(schedule):
        if days_since_sent >= schedule[-1]:
            return FollowUpAction(
                quote_id=quote.quote_id, customer_name=quote.customer_name,
                step=quote.followups_sent + 1, kind="handoff",
                message=(f"{quote.customer_name} hasn't responded to "
                         f"{quote.followups_sent} follow-ups on a "
                         f"${quote.amount:,.0f} quote. Recommend a personal call."),
                days_since_contact=days_since_sent,
            )
        return None

    milestone = schedule[quote.followups_sent]
    if days_since_sent >= milestone:
        step = quote.followups_sent + 1
        return FollowUpAction(
            quote_id=quote.quote_id, customer_name=quote.customer_name,
            step=step, kind="followup",
            message=_compose_message(quote, step, len(schedule)),
            days_since_contact=days_since_sent,
        )
    return None


def run_cycle(quotes: list[Quote], *, today: Optional[date] = None,
              schedule: Optional[list[int]] = None,
              sender: Optional[Sender] = None) -> dict:
    """Process all quotes for `today`: send due follow-ups (via sender), escalate handoffs.

    Mutates each quote's followups_sent/last_contact_date when a follow-up is sent.
    Returns a summary dict. `sender` defaults to an in-memory mock recorder.
    """
    today = today or date.today()
    schedule = schedule or DEFAULT_SCHEDULE_DAYS
    sender = sender or _mock_sender_factory()

    sent_actions: list[FollowUpAction] = []
    handoffs: list[FollowUpAction] = []

    for q in quotes:
        action = next_action(q, today=today, schedule=schedule)
        if action is None:
            continue
        if action.kind == "handoff":
            handoffs.append(action)
            continue
        ok = sender(q.customer_name, action.message)
        if ok:
            q.followups_sent += 1
            q.last_contact_date = today
            sent_actions.append(action)

    return {
        "date": today.isoformat(),
        "quotes_processed": len(quotes),
        "followups_sent": len(sent_actions),
        "handoffs": handoffs,
        "actions": sent_actions,
        "sender": sender,
    }
