"""
EchoFrame fulfillment guard
─────────────────────────────────────────────────────────────────────────────
The email_failsafe net catches a *delivery* failure — an engine tried to send a
finished report and Resend refused (bad domain, bounce, outage). This guards the
OTHER failure mode: the engine never got far enough to send anything, because it
couldn't read the customer's file or crashed mid-generation.

Without this, a paying customer who uploads an unusual file gets total silence —
the exact thing we can't allow. notify_unreadable() guarantees two messages
whenever fulfilment can't complete automatically:

  • the customer gets a calm, honest note — we have your file, a human is finishing
    it personally, you'll hear back within one business day.
  • the owner gets an alert with the reason and the file attached, so it becomes a
    two-minute manual job instead of a lost sale.

It never raises — a guard that throws would defeat its own purpose.
"""

from __future__ import annotations

import os
import base64
import traceback


def _owner() -> str:
    return (os.environ.get("FAILSAFE_EMAIL") or os.environ.get("ALERT_EMAIL")
            or "jacobstarling4313@gmail.com")


def _from() -> str:
    return os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")


def _csv_attachment(raw, filename: str):
    if raw is None:
        return None
    data = raw if isinstance(raw, (bytes, bytearray)) else str(raw).encode("utf-8", "replace")
    return {"filename": filename,
            "content": base64.b64encode(bytes(data)).decode("ascii"),
            "content_type": "text/csv"}


def notify_unreadable(customer_email: str, customer_name: str, product_label: str,
                      *, reason: str = "", raw=None, filename: str = "upload.csv",
                      customer_message: str = "") -> None:
    """Reassure the customer and alert the owner when a paid upload can't be
    fulfilled automatically. Best-effort and silent on its own failures.

    If ``customer_message`` is given (a safe, specific, customer-correctable
    reason — e.g. "this isn't a financials export, please upload your P&L"), the
    customer sees THAT plus a clear next step, instead of the generic "a human is
    finishing it" note. Generic failures (no message) keep the calm default so we
    never leak an internal error to a customer (B-5)."""
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    name = (customer_name or "there").strip() or "there"
    product = (product_label or "your report").strip() or "your report"
    customer_message = (customer_message or "").strip()

    # 1) Customer — either the specific, actionable reason, or the calm generic note.
    try:
        if customer_message:
            body = (
                f'<div style="font-family:Inter,system-ui,Arial,sans-serif;max-width:540px;color:#111827;">'
                f'<p style="font-size:15px;">Hi {name},</p>'
                f'<p style="font-size:15px;line-height:1.6;">Thanks for your <strong>{product}</strong> '
                f'upload. We weren\'t able to generate your report automatically:</p>'
                f'<p style="font-size:15px;line-height:1.6;background:#FDF3E3;border-left:3px solid #94681C;'
                f'padding:12px 14px;border-radius:6px;margin:14px 0;">{customer_message}</p>'
                f'<p style="font-size:15px;line-height:1.6;">Once that\'s sorted, re-upload and you\'ll have '
                f'your report in minutes. Or just reply to this email and Jacob will take care of it for you.</p>'
                f'<p style="font-size:15px;">— EchoFrame</p></div>')
            subject = f"Quick fix needed on your {product} upload"
        else:
            body = (
                f'<div style="font-family:Inter,system-ui,Arial,sans-serif;max-width:540px;color:#111827;">'
                f'<p style="font-size:15px;">Hi {name},</p>'
                f'<p style="font-size:15px;line-height:1.6;">Thanks — we\'ve received your file for '
                f'<strong>{product}</strong>. This one needs a quick personal look from Jacob before we '
                f'generate your report, so he\'s finishing it by hand and will follow up '
                f'<strong>within one business day</strong>.</p>'
                f'<p style="font-size:15px;line-height:1.6;">There\'s nothing you need to do — your upload '
                f'is safe and we\'re on it. If Jacob needs anything from you, he\'ll reach out directly.</p>'
                f'<p style="font-size:15px;">— EchoFrame</p></div>')
            subject = f"We've got your {product} upload"
        resend.Emails.send({"from": _from(), "to": [customer_email],
                            "subject": subject, "html": body})
        print(f"[fulfillment_guard] customer reassured: {customer_email}", flush=True)
    except Exception:
        print(f"[fulfillment_guard] customer note FAILED:\n{traceback.format_exc()}", flush=True)

    # 2) Owner — actionable alert with the file attached.
    try:
        msg = {
            "from": _from(),
            "to": [_owner()],
            "subject": f"[ACTION] Couldn't auto-generate {product} for {customer_email}",
            "html": (
                f'<div style="font-family:system-ui,Arial,sans-serif;color:#111;">'
                f'<p style="font:600 15px system-ui;color:#b91c1c;">A paid upload couldn\'t be generated '
                f'automatically.</p>'
                f'<p>Product: <strong>{product}</strong><br>'
                f'Customer: <strong>{customer_email}</strong> ({name})<br>'
                f'Reason: {reason or "engine produced no report"}</p>'
                f'<p>The customer has been told you\'ll follow up within one business day. Their file is '
                f'attached — generate it manually and send it over.</p></div>'),
        }
        att = _csv_attachment(raw, filename)
        if att:
            msg["attachments"] = [att]
        resend.Emails.send(msg)
        print(f"[fulfillment_guard] owner alerted for {product} / {customer_email}", flush=True)
    except Exception:
        print(f"[fulfillment_guard] owner alert FAILED:\n{traceback.format_exc()}", flush=True)
