"""
EchoFrame — customer-facing input errors
─────────────────────────────────────────────────────────────────────────────
Most failures must NOT be shown to a customer: a stack trace, an internal
assertion, a third-party outage. The safe default for those is the calm generic
note ("we've got your file, a human is finishing it"). See fulfillment_guard.

But some failures are the CUSTOMER's to fix, and saying so plainly saves them a
day of waiting: "this isn't a financials export — please upload your P&L." That
is what CustomerInputError carries.

An engine raises CustomerInputError(customer_message) when BOTH are true:
  • the problem is something the customer can correct themselves, and
  • the message is safe and helpful to show them verbatim (no internals, no PII).

main._run_report_sync catches it and shows `.customer_message` to the customer
instead of the generic note; the owner still gets the full internal detail.
"""

from __future__ import annotations


class CustomerInputError(ValueError):
    """A fulfilment failure whose message is safe to show the customer directly.

    Subclasses ValueError because these ARE input-validation errors — so existing
    `except ValueError` / `pytest.raises(ValueError)` callers keep working, while
    code that wants the customer message catches CustomerInputError specifically
    (and must do so BEFORE a bare `except ValueError`)."""

    def __init__(self, customer_message: str, *, internal: str = ""):
        self.customer_message = (customer_message or "").strip()
        # The Exception text (for logs / owner alert) carries internal detail when
        # given, else falls back to the customer message.
        super().__init__(internal.strip() if internal else self.customer_message)
