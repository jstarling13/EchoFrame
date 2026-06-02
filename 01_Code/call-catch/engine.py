"""
Call Catch — missed-call auto-text engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from revenue/missedcall.html):
  "The second you miss a call, a text goes out. The lead stays warm until you can follow up."
  1. Connect your business number
  2. Missed call triggers an instant text
  3. You follow up on a warm lead   (under-60s response, custom templates,
     missed-call log dashboard, after-hours & weekend coverage)

Pure Python. The SMS sender is INJECTED (mock recorder by default) — no real texts
are sent here. The telephony integration (Twilio/etc. webhook on a missed call) is the
documented seam; this module is the "compose the right text instantly + log it" core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Callable, Optional


DEFAULT_BUSINESS_HOURS = {
    # weekday (0=Mon .. 6=Sun): (open, close) or None if closed
    0: (time(8, 0), time(17, 0)),
    1: (time(8, 0), time(17, 0)),
    2: (time(8, 0), time(17, 0)),
    3: (time(8, 0), time(17, 0)),
    4: (time(8, 0), time(17, 0)),
    5: None,   # Saturday closed
    6: None,   # Sunday closed
}

DEFAULT_TEMPLATES = {
    "business_hours": (
        "Hi! This is {business}. Sorry we missed your call — we're with another customer "
        "and will call you right back. Or reply here and we'll help you now."
    ),
    "after_hours": (
        "Hi! This is {business}. Thanks for calling — we're closed right now but got your "
        "missed call. Reply here with what you need and we'll get back to you first thing."
    ),
}


@dataclass
class MissedCallEvent:
    caller_number: str
    occurred_at: datetime
    after_hours: bool
    message_sent: str
    delivered: bool


def is_after_hours(when: datetime, business_hours: Optional[dict] = None) -> bool:
    business_hours = business_hours or DEFAULT_BUSINESS_HOURS
    window = business_hours.get(when.weekday())
    if window is None:
        return True
    open_t, close_t = window
    return not (open_t <= when.time() < close_t)


Sender = Callable[[str, str], bool]


def _mock_sender_factory():
    sent: list[dict] = []

    def sender(to_number: str, message: str) -> bool:
        sent.append({"to": to_number, "message": message})
        return True

    sender.sent = sent  # type: ignore[attr-defined]
    return sender


def compose_message(business_name: str, after_hours: bool,
                    templates: Optional[dict] = None) -> str:
    templates = templates or DEFAULT_TEMPLATES
    key = "after_hours" if after_hours else "business_hours"
    return templates[key].format(business=business_name)


class CallCatch:
    """Holds config + the missed-call log; sends an instant auto-text per missed call."""

    def __init__(self, business_name: str, *,
                 business_hours: Optional[dict] = None,
                 templates: Optional[dict] = None,
                 sender: Optional[Sender] = None):
        self.business_name = business_name
        self.business_hours = business_hours or DEFAULT_BUSINESS_HOURS
        self.templates = templates or DEFAULT_TEMPLATES
        self.sender = sender or _mock_sender_factory()
        self.log: list[MissedCallEvent] = []
        self._seen_numbers: set[str] = set()

    def handle_missed_call(self, caller_number: str, *,
                           occurred_at: Optional[datetime] = None,
                           dedupe: bool = True) -> MissedCallEvent:
        """Process one missed call: compose + send the auto-text, log it, return the event.

        If `dedupe` is True, a repeat missed call from the same number is logged but not
        re-texted (avoids spamming a caller who rings several times)."""
        occurred_at = occurred_at or datetime.now()
        after = is_after_hours(occurred_at, self.business_hours)
        message = compose_message(self.business_name, after, self.templates)

        already = caller_number in self._seen_numbers
        delivered = False
        if not (dedupe and already):
            delivered = self.sender(caller_number, message)
            self._seen_numbers.add(caller_number)

        event = MissedCallEvent(
            caller_number=caller_number, occurred_at=occurred_at,
            after_hours=after, message_sent=message if delivered else "",
            delivered=delivered,
        )
        self.log.append(event)
        return event

    def dashboard(self) -> dict:
        return {
            "business": self.business_name,
            "total_missed_calls": len(self.log),
            "texts_sent": sum(1 for e in self.log if e.delivered),
            "after_hours_calls": sum(1 for e in self.log if e.after_hours),
            "unique_callers": len(self._seen_numbers),
            "log": self.log,
        }
