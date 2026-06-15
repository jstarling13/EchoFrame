"""
Tests for email_failsafe.install() using a fake `resend` module — no network,
no real SDK required. Run:  python3 test_email_failsafe.py
"""
import sys
import types
import os

os.environ["FAILSAFE_EMAIL"] = "owner@example.com"
os.environ["RESEND_API_KEY"] = "test-key"

# ── Build a fake `resend` module ────────────────────────────────────────────
sent: list = []          # every params dict that actually "went out"
fail_primary = {"on": False}

def _fake_send(params, *a, **k):
    # Simulate Resend rejecting sends from an unverified domain, but accepting
    # the onboarding@resend.dev fallback.
    frm = params.get("from", "")
    if fail_primary["on"] and "onboarding@resend.dev" not in frm:
        raise RuntimeError("validation_error: domain is not verified")
    sent.append(params)
    return {"id": "msg_fake"}

fake_resend = types.ModuleType("resend")
fake_resend.api_key = ""
fake_resend.Emails = types.SimpleNamespace(send=_fake_send)
sys.modules["resend"] = fake_resend

# ── Install the failsafe ────────────────────────────────────────────────────
import email_failsafe
email_failsafe.install()
import resend  # now the wrapped module

PRIMARY = {
    "from": "EchoFrame <jacob.starling@echoframe.net>",
    "to": ["client@business.com"],
    "subject": "Your EchoFrame report",
    "html": "<h1>Report body</h1>",
    "attachments": [{"filename": "report.pdf", "content": "BASE64", "content_type": "application/pdf"}],
}

failures = []

# ── Test 1: happy path is untouched ─────────────────────────────────────────
sent.clear(); fail_primary["on"] = False
resend.Emails.send(dict(PRIMARY))
if len(sent) == 1 and sent[0]["to"] == ["client@business.com"]:
    print("PASS  happy path delivers to client unchanged")
else:
    failures.append(f"happy path: unexpected sent={sent}")

# ── Test 2: primary fails → owner gets the fallback with the attachment ──────
sent.clear(); fail_primary["on"] = True
result = resend.Emails.send(dict(PRIMARY))
checks = {
    "swallowed exception (returned None)": result is None,
    "exactly one fallback went out": len(sent) == 1,
    "fallback addressed to owner": sent and sent[0]["to"] == ["owner@example.com"],
    "fallback from onboarding@resend.dev": sent and "onboarding@resend.dev" in sent[0]["from"],
    "client address shown in subject": sent and "client@business.com" in sent[0]["subject"],
    "report attachment carried over": sent and sent[0].get("attachments") == PRIMARY["attachments"],
    "original report html preserved": sent and "Report body" in sent[0]["html"],
}
for label, ok in checks.items():
    if ok:
        print(f"PASS  {label}")
    else:
        failures.append(f"fallback: {label} — got {sent}")

# ── Test 3: idempotent install ──────────────────────────────────────────────
before = resend.Emails.send
email_failsafe.install()
if resend.Emails.send is before:
    print("PASS  install() is idempotent (no double-wrap)")
else:
    failures.append("install() double-wrapped")

# ── Test 4: fallback ALSO failing never raises ──────────────────────────────
sent.clear()
def _always_fail(params, *a, **k):
    raise RuntimeError("everything is down")
# rebuild a fresh wrapped stack around an always-failing sender
fake2 = types.ModuleType("resend")
fake2.api_key = ""
fake2.Emails = types.SimpleNamespace(send=_always_fail)
sys.modules["resend"] = fake2
import importlib
importlib.reload(email_failsafe)
email_failsafe.install()
import resend as resend2
try:
    r = resend2.Emails.send(dict(PRIMARY))
    print("PASS  total outage swallowed (no crash), returned", r)
except Exception as e:
    failures.append(f"total outage raised: {e!r}")

print()
if failures:
    print("FAILED:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("ALL TESTS PASSED")
