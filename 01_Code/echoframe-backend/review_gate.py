"""
EchoFrame human-review gate
─────────────────────────────────────────────────────────────────────────────
EchoFrame advertises that *a real analyst reviews every report before it goes
out*. This module makes that promise literally true without touching any of the
15 product engines.

Like ``email_failsafe``, it wraps the single send choke-point
``resend.Emails.send`` exactly once at startup (call ``install()`` AFTER
``email_failsafe.install()`` so the review copies are themselves fail-safe).

Behaviour when ``REVIEW_MODE`` is on (the default):

  • A customer-bound email that carries a **report attachment** is NOT sent to
    the customer. Instead it is held server-side and a review copy — the real
    report, plus an "Approve & send" and a "Hold" link — is emailed to the
    owner. The engine sees a normal success return and keeps running.
  • Clicking "Approve & send" hits ``/api/review/approve`` which calls
    ``release()`` → the original email is delivered to the customer for real
    (still fail-safe protected).
  • Transactional mail with no attachment (upload links, owner alerts, the
    review copy itself) is never gated — it goes out immediately.

Set ``REVIEW_MODE`` to ``off`` (or ``0``/``false``/``no``) to disable the gate
entirely and return to instant auto-send — e.g. for stretches when the owner
can't review. The wrap becomes a transparent pass-through.

Config (env):
  REVIEW_MODE       — on (default) | off
  ALERT_EMAIL       — owner inbox the review copy goes to
  EMAIL_FROM        — verified-domain From used for the review copy
  PUBLIC_BASE_URL   — base URL for the approve/hold links (the backend's own
                      public URL; falls back to the Railway URL)
  REVIEW_TTL_DAYS   — how long a held report stays approvable (default 14)
"""

from __future__ import annotations

import os
import re
import time
import secrets
from uuid import uuid4

import store

_INSTALLED_ATTR = "_echoframe_review_installed"

# Captured at install(): the send function we wrap (the fail-safe-wrapped one).
_underlying_send = None

_FAILSAFE_FROM_MARK = "onboarding@resend.dev"
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


# ── config helpers ──────────────────────────────────────────────────────────

def _mode_on() -> bool:
    return os.environ.get("REVIEW_MODE", "on").strip().lower() not in (
        "off", "0", "false", "no", "",
    )


def _ttl_seconds() -> int:
    try:
        return int(float(os.environ.get("REVIEW_TTL_DAYS", "14")) * 86400)
    except Exception:
        return 14 * 86400


def _owner_email() -> str:
    return os.environ.get("ALERT_EMAIL", "jacob.starling@echoframe.net").strip()


def _from_address() -> str:
    return os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")


# Optional runtime override for the approve/hold link host (used by the
# production self-test so the button always points back at the same server).
_base_override = None


def set_base_url(url) -> None:
    global _base_override
    _base_override = url.rstrip("/") if url else None


def _base_url() -> str:
    if _base_override:
        return _base_override
    return (
        os.environ.get("PUBLIC_BASE_URL")
        or "https://echoframe-production.up.railway.app"
    ).rstrip("/")


def _default_delay_minutes() -> int:
    """Global send delay after approval (env REVIEW_SEND_DELAY_MINUTES). 0 = now."""
    try:
        return max(0, int(float(os.environ.get("REVIEW_SEND_DELAY_MINUTES", "0"))))
    except Exception:
        return 0


def _owner_addresses() -> set[str]:
    addrs = set()
    for raw in (
        _owner_email(),
        os.environ.get("FAILSAFE_EMAIL", "jacobstarling4313@gmail.com"),
        _from_address(),
    ):
        m = _EMAIL_RE.search(raw or "")
        if m:
            addrs.add(m.group(0).lower())
    return addrs


# ── classification ──────────────────────────────────────────────────────────

def _recipients(params: dict) -> list[str]:
    to = params.get("to")
    if isinstance(to, (list, tuple)):
        out = []
        for x in to:
            m = _EMAIL_RE.search(str(x))
            out.append(m.group(0).lower() if m else str(x).lower())
        return out
    if to:
        m = _EMAIL_RE.search(str(to))
        return [m.group(0).lower() if m else str(to).lower()]
    return []


def _should_review(params: dict) -> bool:
    """Gate only customer-bound emails that actually carry a report."""
    if not _mode_on():
        return False
    if params.get("_review_bypass"):
        return False
    # Gate anything that carries a report attachment, OR is explicitly flagged for
    # review (e.g. AI-written Quote Revive digests that have no attachment). Plain
    # transactional mail (upload links, owner alerts) still passes straight through.
    if not params.get("attachments") and not params.get("_force_review"):
        return False
    if _FAILSAFE_FROM_MARK in str(params.get("from", "")):
        return False
    recips = _recipients(params)
    if not recips:
        return False
    owners = _owner_addresses()
    if all(r in owners for r in recips):       # owner-only mail → pass through
        return False
    return True


# ── the held-for-review flow ────────────────────────────────────────────────

def _recipient_label(params: dict) -> str:
    to = params.get("to")
    if isinstance(to, (list, tuple)):
        return ", ".join(str(x) for x in to)
    return str(to) if to else "(unknown recipient)"


def _dq_banner(params: dict) -> str:
    """A red 'check the data first' banner for the review email, built from the
    data-quality warnings the engine rode along in `_dq_warnings`. Empty string
    when the file looked clean."""
    warnings = params.get("_dq_warnings") or []
    if not warnings:
        return ""
    items = "".join(
        f"<li style='margin:2px 0'>{w}</li>" for w in warnings
    )
    return (
        "<div style='border:1px solid #fca5a5;background:#fef2f2;border-radius:8px;"
        "padding:14px 16px;margin:0 0 18px'>"
        "<p style='font:700 14px system-ui;color:#b91c1c;margin:0 0 6px'>"
        "⚠ Check the data before approving</p>"
        "<p style='font:13px system-ui;color:#7f1d1d;margin:0 0 8px'>"
        "The uploaded file looked messy. The report was still generated, but these "
        "may be wrong — verify them against the file before you release it:</p>"
        f"<ul style='font:13px system-ui;color:#7f1d1d;margin:0;padding-left:18px'>{items}</ul>"
        "</div>"
    )


def _review_email(review_id: str, token: str, params: dict) -> dict:
    base = _base_url()
    approve = f"{base}/api/review/approve?id={review_id}&t={token}"
    hold = f"{base}/api/review/hold?id={review_id}&t={token}"
    intended = _recipient_label(params)
    subject = params.get("subject") or "EchoFrame report"

    btn = (
        "display:inline-block;padding:13px 26px;border-radius:8px;"
        "font:600 15px system-ui;text-decoration:none;"
    )
    body = (
        f"<div style='font:14px system-ui;color:#0a274f;max-width:620px'>"
        f"{_dq_banner(params)}"
        f"<p style='font:700 16px system-ui;color:#0a274f;margin:0 0 4px'>"
        f"Human review — approve to release</p>"
        f"<p style='color:#374151;margin:0 0 16px'>This report is ready and is "
        f"<strong>waiting on your review</strong>. Nothing has been sent to the "
        f"customer yet.</p>"
        f"<table style='font:14px system-ui;color:#111;border-collapse:collapse;margin-bottom:18px'>"
        f"<tr><td style='color:#6b7280;padding:2px 12px 2px 0'>Customer</td>"
        f"<td><strong>{intended}</strong></td></tr>"
        f"<tr><td style='color:#6b7280;padding:2px 12px 2px 0'>Subject</td>"
        f"<td>{subject}</td></tr></table>"
        f"<p style='margin:0 0 22px'>"
        f"<a href='{approve}' style='{btn}background:#0a274f;color:#fff'>Approve &amp; send</a>"
        f"&nbsp;&nbsp;"
        f"<a href='{hold}' style='{btn}background:#f3f4f6;color:#0a274f'>Hold / I'll edit</a>"
        f"</p>"
        f"<p style='color:#6b7280;font-size:12px;margin:0 0 18px'>"
        f"The finished report is attached below — review it, then approve to "
        f"deliver it to the customer from your verified address.</p>"
        f"<hr style='border:none;border-top:1px solid #e5e7eb'>"
        f"<p style='color:#9ca3af;font-size:12px'>Preview of the customer email:</p>"
        f"{params.get('html') or ''}"
        f"</div>"
    )

    review = {
        "from": _from_address(),
        "to": [_owner_email()],
        "subject": f"[REVIEW] {subject} → {intended}",
        "html": body,
        "_review_bypass": True,
    }
    if params.get("attachments"):
        review["attachments"] = params["attachments"]
    return review


def _hold_for_review(params: dict) -> dict:
    review_id = uuid4().hex[:16]
    token = secrets.token_urlsafe(24)
    record = {
        "params": params,
        "token": token,
        "status": "pending",
        "created": int(time.time()),
        "to": _recipient_label(params),
        "subject": params.get("subject", ""),
    }
    store.set_json(f"review:{review_id}", record, ex=_ttl_seconds())
    try:
        store.set_add("review:pending", review_id)
    except Exception:
        pass

    # Send the review copy via the underlying (fail-safe) sender so it never
    # re-enters this gate and is itself protected.
    sender = _underlying_send
    try:
        sender(_review_email(review_id, token, params))
        print(f"[review_gate] held report {review_id} → owner review sent.")
    except Exception as e:  # never break fulfilment
        print(f"[review_gate] review copy failed ({e!r}); report still held.")

    # Mimic a normal Resend success so the engine keeps running.
    return {"id": f"review-held-{review_id}"}


# ── public API used by the approve/hold endpoints ───────────────────────────

def peek(review_id: str):
    """Return the stored review record (or None)."""
    return store.get_json(f"review:{review_id}")


def release(review_id: str, delay_minutes=None):
    """Deliver a held report to its real customer on approval.

    Sends immediately by default. If a delay is configured — either the
    REVIEW_SEND_DELAY_MINUTES env var or an explicit ``delay_minutes`` (e.g.
    from an approve link) — the customer send is SCHEDULED that many minutes
    out via Resend's ``scheduled_at`` instead of going immediately.
    """
    rec = store.get_json(f"review:{review_id}")
    if not rec or rec.get("status") != "pending":
        return rec
    sender = _underlying_send
    if sender is None:
        import resend
        sender = resend.Emails.send

    dmin = _default_delay_minutes() if delay_minutes is None else max(0, int(delay_minutes))
    params = dict(rec["params"])
    params.pop("_dq_warnings", None)  # internal review-only note; never to the customer
    if dmin > 0:
        from datetime import datetime, timezone, timedelta
        params["scheduled_at"] = (
            datetime.now(timezone.utc) + timedelta(minutes=dmin)
        ).isoformat()

    out = sender(params)
    rec["status"] = "approved"
    rec["released"] = int(time.time())
    rec["delay_minutes"] = dmin
    store.set_json(f"review:{review_id}", rec, ex=_ttl_seconds())
    try:
        store.set_remove("review:pending", review_id)
    except Exception:
        pass
    when = f"scheduled to send in {dmin} min" if dmin else "delivered now"
    print(f"[review_gate] report {review_id} approved → {when} to customer.")
    return out


def hold(review_id: str):
    """Mark a held report as held (owner will edit / resend manually)."""
    rec = store.get_json(f"review:{review_id}")
    if not rec:
        return None
    rec["status"] = "held"
    store.set_json(f"review:{review_id}", rec, ex=_ttl_seconds())
    try:
        store.set_remove("review:pending", review_id)
    except Exception:
        pass
    return rec


# ── installer ───────────────────────────────────────────────────────────────

def install() -> None:
    """Wrap ``resend.Emails.send`` with the review gate. Idempotent."""
    global _underlying_send
    import resend

    current = resend.Emails.send
    if getattr(current, _INSTALLED_ATTR, False):
        return
    _underlying_send = current  # the fail-safe-wrapped sender

    def gated_send(params, *args, **kwargs):
        try:
            if isinstance(params, dict) and _should_review(params):
                return _hold_for_review(params)
        except Exception as e:
            print(f"[review_gate] gate error ({e!r}); sending normally.")
        # Not held for review (gate off, or owner/transactional mail) → strip the
        # internal review-only note so it never travels with a real send.
        if isinstance(params, dict) and "_dq_warnings" in params:
            params = {k: v for k, v in params.items() if k != "_dq_warnings"}
        return current(params, *args, **kwargs)

    setattr(gated_send, _INSTALLED_ATTR, True)
    resend.Emails.send = gated_send
    print(f"[review_gate] installed (REVIEW_MODE={'on' if _mode_on() else 'off'}).")
