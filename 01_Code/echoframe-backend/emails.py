"""
EchoFrame transactional emails (renewal fulfilment loop)
─────────────────────────────────────────────────────────────────────────────
Three messages drive the recurring-fulfilment loop, all sent via Resend:

  1. send_upload_link  — "send me this month's numbers" after a renewal is billed
  2. send_reminder     — nudge a client who hasn't uploaded within 4 days
  3. send_owner_alert  — tell the owner (jacob.starling@echoframe.net) a client
                         is overdue, so it can be chased personally

The report-delivery email itself is unchanged — each product engine still sends
the finished report via Resend after a valid upload. This module only covers the
"ask for the files" and "nobody uploaded" cases.

Config (env):
  RESEND_API_KEY   — Resend auth (already required by the engines)
  EMAIL_FROM       — client-facing From, e.g. "EchoFrame <jacob.starling@echoframe.net>"
  ALERT_EMAIL      — where overdue alerts go (defaults to jacob.starling@echoframe.net)
"""

from __future__ import annotations

import os
import resend

# Sensible defaults; override in production via env. Note the engines historically
# defaulted to the ".co" domain — the real sending domain is echoframe.net.
EMAIL_FROM  = os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "jacob.starling@echoframe.net")

_DISCLAIMER = (
    '<p style="color:#6B7280;font-size:12px;">Business intelligence, not accounting '
    "software. Informational only; not accounting, tax, legal, or investment advice.</p>"
)


def _send(params: dict) -> None:
    """Single choke-point for Resend so the API key is set consistently and no
    PII is ever logged."""
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    resend.Emails.send(params)


def send_upload_link(
    to_email: str,
    name: str,
    product_label: str,
    upload_url: str,
    period_label: str = "",
) -> None:
    """Email a client their secure upload link for the period just billed."""
    greeting = (name or "").strip() or "there"
    when = f" for {period_label}" if period_label else ""
    subject = f"Send me this month's numbers — your {product_label}"
    html = (
        f"<p>Hi {greeting},</p>"
        f"<p>Your subscription for the <strong>{product_label}</strong> just renewed{when}, "
        f"so it's time to pull this month's report together.</p>"
        f"<p>Use your secure link below to drop in this month's file — your report is generated "
        f"and emailed back to you within minutes:</p>"
        f'<p><a href="{upload_url}" '
        f'style="display:inline-block;background:#1E90FF;color:#fff;font-weight:600;'
        f'padding:12px 22px;border-radius:8px;text-decoration:none;">Upload this month’s file</a></p>'
        f'<p style="color:#6B7280;font-size:13px;">Or paste this link into your browser:<br>{upload_url}</p>'
        f"<p>Reply to this email if anything looks off.</p>"
        f"<p>— EchoFrame</p>"
        f"{_DISCLAIMER}"
    )
    _send({"from": EMAIL_FROM, "to": [to_email], "subject": subject, "html": html})


def send_reminder(
    to_email: str,
    name: str,
    product_label: str,
    upload_url: str,
    period_label: str = "",
) -> None:
    """Resend the upload link to a client who hasn't uploaded yet."""
    greeting = (name or "").strip() or "there"
    when = f" for {period_label}" if period_label else " this month"
    subject = f"Reminder: still need your numbers{(' for ' + period_label) if period_label else ''}"
    html = (
        f"<p>Hi {greeting},</p>"
        f"<p>Just a friendly nudge — we haven’t received your file{when} yet for your "
        f"<strong>{product_label}</strong>, so your report is on hold until it comes in.</p>"
        f"<p>It only takes a minute:</p>"
        f'<p><a href="{upload_url}" '
        f'style="display:inline-block;background:#1E90FF;color:#fff;font-weight:600;'
        f'padding:12px 22px;border-radius:8px;text-decoration:none;">Upload now</a></p>'
        f'<p style="color:#6B7280;font-size:13px;">Or paste this link into your browser:<br>{upload_url}</p>'
        f"<p>Already sent it? You can ignore this.</p>"
        f"<p>— EchoFrame</p>"
        f"{_DISCLAIMER}"
    )
    _send({"from": EMAIL_FROM, "to": [to_email], "subject": subject, "html": html})


def send_login_link(to_email: str, name: str, login_url: str) -> None:
    """Email a client their one-tap, single-use magic link to sign in to the
    portal. No password is ever set or stored."""
    greeting = (name or "").strip() or "there"
    subject = "Your EchoFrame sign-in link"
    html = (
        f"<p>Hi {greeting},</p>"
        f"<p>Here's your secure link to sign in to your EchoFrame account. It works "
        f"once and expires in 20 minutes:</p>"
        f'<p><a href="{login_url}" '
        f'style="display:inline-block;background:#1E90FF;color:#fff;font-weight:600;'
        f'padding:12px 22px;border-radius:8px;text-decoration:none;">Sign in to EchoFrame</a></p>'
        f'<p style="color:#6B7280;font-size:13px;">Or paste this link into your browser:<br>{login_url}</p>'
        f"<p style=\"color:#6B7280;font-size:13px;\">If you didn't request this, you can safely ignore "
        f"this email — no one can sign in without this link.</p>"
        f"<p>— EchoFrame</p>"
        f"{_DISCLAIMER}"
    )
    _send({"from": EMAIL_FROM, "to": [to_email], "subject": subject, "html": html})


def send_owner_alert(
    client_email: str,
    client_name: str,
    product_label: str,
    period_label: str,
    days_overdue: int,
) -> None:
    """Alert the owner that a billed client hasn't uploaded their files."""
    subject = f"⚠ No upload yet: {client_name or client_email} ({product_label})"
    html = (
        f"<p>Heads up — a client was billed but hasn’t uploaded their files:</p>"
        f"<ul>"
        f"<li><strong>Client:</strong> {client_name or '(name unknown)'} &lt;{client_email}&gt;</li>"
        f"<li><strong>Product:</strong> {product_label}</li>"
        f"<li><strong>Period:</strong> {period_label or '(current)'}</li>"
        f"<li><strong>Days since billed:</strong> {days_overdue}</li>"
        f"</ul>"
        f"<p>A reminder was just re-sent to the client automatically. You may want to follow up personally.</p>"
        f"<p>— EchoFrame system</p>"
    )
    _send({"from": EMAIL_FROM, "to": [ALERT_EMAIL], "subject": subject, "html": html})


def send_intake_confirmation(
    to_email: str,
    name: str,
    reference: str,
    area_label: str,
    product_name: str,
    file_count: int,
) -> None:
    """Confirm a Free First Look submission. No file contents or financial
    figures are echoed back — just what was received and what happens next."""
    greeting = (name or "").strip() or "there"
    files_line = (
        f"We also received {file_count} file{'s' if file_count != 1 else ''}."
        if file_count else "You didn't attach a file, and that's fine for a first look."
    )
    subject = f"We've got your EchoFrame first look ({reference})"
    html = (
        f"<p>Hi {greeting},</p>"
        f"<p>Thanks for telling us where things feel unclear. Here's what we received:</p>"
        f"<ul>"
        f"<li><strong>Reference:</strong> {reference}</li>"
        f"<li><strong>Area:</strong> {area_label}</li>"
        f"<li><strong>Starting point:</strong> {product_name}</li>"
        f"</ul>"
        f"<p>{files_line}</p>"
        f"<p><strong>What happens next:</strong> a person checks what you shared, confirms "
        f"the recommended starting point, and replies with the next step. You'll hear back "
        f"within 48 hours.</p>"
        f"<p style=\"color:#6B7280;font-size:13px;\">Need to correct or add something? Just reply "
        f"to this email and mention reference {reference}.</p>"
        f"<p>— EchoFrame</p>"
        f"{_DISCLAIMER}"
    )
    _send({"from": EMAIL_FROM, "to": [to_email], "subject": subject, "html": html})


def send_intake_owner_alert(
    reference: str,
    area_label: str,
    product_name: str,
    business_name: str,
    contact_name: str,
    contact_email: str,
    contact_phone: str,
    summary: str,
    attachments: list[dict] | None = None,
) -> None:
    """Alert the owner to a new Free First Look lead. Unlike customer-facing mail,
    this one carries full detail — it's an internal working alert, not a public
    message — and any uploaded files come along as attachments so it's a two-
    minute follow-up instead of a second round trip to find the file."""
    subject = f"New first look ({area_label}): {business_name or contact_email}"
    html = (
        f"<p>New Free First Look submission:</p>"
        f"<ul>"
        f"<li><strong>Reference:</strong> {reference}</li>"
        f"<li><strong>Area:</strong> {area_label}</li>"
        f"<li><strong>Recommended product:</strong> {product_name}</li>"
        f"<li><strong>Business:</strong> {business_name or '(not given)'}</li>"
        f"<li><strong>Contact:</strong> {contact_name or '(no name)'} &lt;{contact_email}&gt;"
        f"{' · ' + contact_phone if contact_phone else ''}</li>"
        f"</ul>"
        f"<p><strong>What they said:</strong><br>{summary or '(no summary provided)'}</p>"
        f"<p>Reply to {contact_email} within 48 hours.</p>"
    )
    msg = {"from": EMAIL_FROM, "to": [ALERT_EMAIL], "subject": subject, "html": html}
    if attachments:
        msg["attachments"] = attachments
    _send(msg)
