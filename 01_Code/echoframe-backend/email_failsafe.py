"""
EchoFrame email failsafe
─────────────────────────────────────────────────────────────────────────────
A single, app-wide safety net so a paying client is NEVER left empty-handed.

Every product engine delivers its finished report by calling
``resend.Emails.send(...)`` directly. If that call fails for any reason — an
unverified sending domain, a mistyped customer address, a hard bounce, a Resend
outage — the customer would silently receive nothing and the owner would never
know.

``install()`` wraps ``resend.Emails.send`` exactly once at startup. Behaviour:

  • Normal path: the real send runs unchanged. Zero behavioural difference when
    everything works.
  • Failure path: the report is re-sent to the OWNER's inbox using Resend's
    always-deliverable ``onboarding@resend.dev`` sender (which delivers to the
    Resend account owner regardless of domain verification), carrying the same
    attachments plus the client's address — so the owner can forward it in
    seconds. The original exception is swallowed afterwards so the background
    worker doesn't crash mid-fulfilment.

This touches no engine code. It is idempotent (safe to call more than once).

Config (env):
  RESEND_API_KEY  — Resend auth (already required by the engines)
  FAILSAFE_EMAIL  — owner inbox that the fallback copy goes to. MUST be the
                    Resend account-owner address, because onboarding@resend.dev
                    only delivers there. Defaults to the current owner.
"""

from __future__ import annotations

import os
import threading

# Per-thread count of delivery ATTEMPTS (calls into resend.Emails.send) since the
# last reset. The fulfilment runner uses this to detect the silent-failure case:
# an engine that raised or returned before ever trying to send anything.
_scope = threading.local()


def reset_calls() -> None:
    _scope.calls = 0


def calls() -> int:
    return int(getattr(_scope, "calls", 0))

# onboarding@resend.dev is Resend's shared sender; it delivers ONLY to the
# Resend account owner's address, with no domain verification required — which
# is exactly what we want for an owner-only failsafe alert.
_FAILSAFE_FROM = "EchoFrame Failsafe <onboarding@resend.dev>"

# Marker so we never double-wrap.
_INSTALLED_ATTR = "_echoframe_failsafe_installed"


def _failsafe_recipient() -> str:
    return os.environ.get("FAILSAFE_EMAIL", "jacobstarling4313@gmail.com")


def _describe_recipient(params: dict) -> str:
    to = params.get("to")
    if isinstance(to, (list, tuple)):
        return ", ".join(str(x) for x in to)
    return str(to) if to else "(unknown recipient)"


def _build_fallback(params: dict, error: Exception) -> dict:
    """Construct the owner-facing fallback message from a failed send."""
    intended = _describe_recipient(params)
    subject = params.get("subject") or "EchoFrame report"
    body = (
        f"<p style=\"font:600 15px system-ui;color:#b91c1c;\">"
        f"Automatic delivery to <strong>{intended}</strong> failed.</p>"
        f"<p style=\"font:14px system-ui;color:#111;\">"
        f"Reason: {type(error).__name__}: {error}</p>"
        f"<p style=\"font:14px system-ui;color:#111;\">"
        f"The client's report is attached below — forward it to "
        f"<strong>{intended}</strong> to complete the order.</p>"
        f"<hr><p style=\"font:13px system-ui;color:#6b7280;\">"
        f"Original subject: {subject}</p>"
    )
    fallback = {
        "from": _FAILSAFE_FROM,
        "to": [_failsafe_recipient()],
        "subject": f"[DELIVERY FAILED → forward me] {subject} — for {intended}",
        "html": body + (params.get("html") or ""),
    }
    # Carry the report itself so the owner can forward it directly.
    if params.get("attachments"):
        fallback["attachments"] = params["attachments"]
    return fallback


def install() -> None:
    """Wrap ``resend.Emails.send`` with the failsafe. Idempotent."""
    import resend

    original = resend.Emails.send
    if getattr(original, _INSTALLED_ATTR, False):
        return  # already wrapped

    def resilient_send(params, *args, **kwargs):
        try:
            _scope.calls = int(getattr(_scope, "calls", 0)) + 1  # count the attempt
        except Exception:
            pass
        try:
            return original(params, *args, **kwargs)
        except Exception as error:  # primary delivery failed
            print(
                f"[email_failsafe] primary send failed "
                f"({type(error).__name__}); routing copy to owner inbox."
            )
            try:
                resend.api_key = os.environ.get("RESEND_API_KEY", "")
                original(_build_fallback(params, error))
                print("[email_failsafe] owner fallback delivered.")
            except Exception as inner:
                # Last resort: never raise out of the failsafe itself.
                print(f"[email_failsafe] fallback ALSO failed: {inner!r}")
            return None  # swallow so the fulfilment worker keeps running

    setattr(resilient_send, _INSTALLED_ATTR, True)
    resend.Emails.send = resilient_send
    print("[email_failsafe] installed (report delivery is now fail-safe).")
