"""
email_sender.py — Resend API wrapper for outbound email delivery.

Resend is already integrated in the EchoFrame backend for report delivery.
We reuse the same API key here for cold outreach. Resend provides:
  - Delivery receipts via webhooks
  - Message IDs for tracking opens/clicks
  - Domain authentication (SPF/DKIM) to avoid spam folders

CAN-SPAM compliance (15 U.S.C. § 7704):
  - Every outgoing email gets a plain-text footer with physical address + opt-out.
  - Recipients on the suppression list are skipped before any API call is made.
  - Suppression list lives in modules/outreach/suppression.txt (one email per line).
    reply_reader.py adds addresses to this file when "stop/unsubscribe" intent
    is detected.
"""

import os
import re

import resend
from config import cfg

resend.api_key = cfg.resend_api_key

# ── Suppression list ──────────────────────────────────────────────────────────
# Path relative to the project root (where main.py lives).
_SUPPRESSION_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "suppression.txt"
)


def _load_suppression_set() -> set[str]:
    """
    Reads suppression.txt and returns a set of lowercased email addresses.
    Creates the file if it doesn't exist so downstream writes never fail.
    """
    os.makedirs(os.path.dirname(_SUPPRESSION_FILE), exist_ok=True)
    if not os.path.exists(_SUPPRESSION_FILE):
        open(_SUPPRESSION_FILE, "w").close()  # touch
        return set()
    with open(_SUPPRESSION_FILE, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def add_to_suppression(email: str) -> None:
    """
    Appends an email address to the suppression list.
    Called by reply_reader.py when a stop/unsubscribe reply is detected.
    Idempotent — won't duplicate if already present.
    """
    email = email.strip().lower()
    existing = _load_suppression_set()
    if email not in existing:
        os.makedirs(os.path.dirname(_SUPPRESSION_FILE), exist_ok=True)
        with open(_SUPPRESSION_FILE, "a", encoding="utf-8") as f:
            f.write(email + "\n")
        print(f"[Suppression] Added {email} to opt-out list.")


def is_suppressed(email: str) -> bool:
    """Returns True if the address is on the opt-out list."""
    return email.strip().lower() in _load_suppression_set()


# ── CAN-SPAM footer ───────────────────────────────────────────────────────────

def _can_spam_footer() -> str:
    """
    Builds the mandatory CAN-SPAM plain-text footer.
    Requires config fields physical_mailing_address and unsubscribe_url_or_email
    to be set (not left as TODO placeholders).
    """
    addr = cfg.physical_mailing_address
    unsub = cfg.unsubscribe_url_or_email
    return (
        "\n\n---\n"
        f"{cfg.from_name}\n"
        f"{addr}\n\n"
        f"To opt out of future emails, reply STOP or contact {unsub}. "
        "We honor all opt-out requests within 10 business days."
    )


# ── Send helpers ──────────────────────────────────────────────────────────────

def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body_text: str,
    reply_to: str | None = None,
) -> str | None:
    """
    Sends a plain-text cold email via Resend.
    Returns the Resend message ID on success, None on failure.

    Skips suppressed addresses before making any API call.
    Appends a CAN-SPAM-compliant footer to every message.

    Plain text only — HTML emails trigger spam filters for cold outreach.
    """
    # ── Suppression check (CAN-SPAM §7704(a)(4)) ─────────────────────────────
    if is_suppressed(to_email):
        print(f"[Suppression] Skipped suppressed address: {to_email}")
        return None

    # ── Append mandatory footer ───────────────────────────────────────────────
    full_body = body_text + _can_spam_footer()

    try:
        params = resend.Emails.SendParams(
            from_=f"{cfg.from_name} <{cfg.from_email}>",
            to=[f"{to_name} <{to_email}>"],
            subject=subject,
            text=full_body,
            reply_to=reply_to or cfg.from_email,
        )
        result = resend.Emails.send(params)
        message_id = result.get("id") or result.id
        print(f"[Resend] Sent to {to_email} — ID: {message_id}")
        return message_id
    except Exception as e:
        print(f"[Resend] Failed to send to {to_email}: {e}")
        return None


def send_bulk_scheduled(
    emails: list[dict],
) -> list[tuple[str, str | None]]:
    """
    Sends a list of emails. Each dict must have:
      to_email, to_name, subject, body_text

    Returns list of (to_email, message_id_or_None).
    Suppressed addresses produce (email, None) without any API call.
    Does NOT enforce send windows — that's the sequence_manager's job.
    """
    results = []
    for e in emails:
        msg_id = send_email(
            to_email=e["to_email"],
            to_name=e["to_name"],
            subject=e["subject"],
            body_text=e["body_text"],
        )
        results.append((e["to_email"], msg_id))
    return results
