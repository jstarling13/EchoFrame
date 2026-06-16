"""Offline tests for review_gate (stubs resend; uses store's in-memory fallback)."""
import os, sys, types

os.environ["REVIEW_MODE"] = "on"
os.environ["ALERT_EMAIL"] = "jacob.starling@echoframe.net"
os.environ["EMAIL_FROM"] = "EchoFrame <jacob.starling@echoframe.net>"
os.environ.setdefault("PUBLIC_BASE_URL", "https://echoframe-production.up.railway.app")

# Fake the resend SDK so nothing hits the network.
sent = []
fake = types.ModuleType("resend")
class _Emails:
    @staticmethod
    def send(params, *a, **k):
        sent.append(params)
        return {"id": f"real-{len(sent)}"}
fake.Emails = _Emails
fake.api_key = ""
sys.modules["resend"] = fake

import review_gate
review_gate.install()
import resend  # now resend.Emails.send is the gated wrapper

def report(to):
    return {
        "from": "EchoFrame <jacob.starling@echoframe.net>",
        "to": [to],
        "subject": "Your May 2026 Auto Ledger — Test Co",
        "html": "<p>your report</p>",
        "attachments": [{"filename": "r.html", "content": "AAAA", "content_type": "text/html"}],
    }

results = {}

# 1) customer report is HELD (owner gets review copy, customer gets nothing yet)
sent.clear()
res = resend.Emails.send(report("client@acme.com"))
held_ok = (
    isinstance(res, dict) and str(res.get("id", "")).startswith("review-held-")
    and len(sent) == 1
    and sent[0]["to"] == ["jacob.starling@echoframe.net"]
    and "[REVIEW]" in sent[0]["subject"]
    and "client@acme.com" in sent[0]["subject"]   # owner sees who it's for
)
results["customer report is held for owner review"] = held_ok

# ...then approving releases it to the real customer
rid = str(res.get("id", "")).replace("review-held-", "")
sent.clear()
review_gate.release(rid)
release_ok = len(sent) == 1 and sent[0]["to"] == ["client@acme.com"] and sent[0].get("attachments")
results["approval delivers to the real customer"] = release_ok

# re-approving is a no-op (status now approved)
sent.clear()
review_gate.release(rid)
results["double-approve does not re-send"] = len(sent) == 0

# 2) transactional mail (no attachment) passes straight through
sent.clear()
resend.Emails.send({"from": "x", "to": ["client@acme.com"], "subject": "your link", "html": "x"})
results["transactional mail is not gated"] = len(sent) == 1 and sent[0]["to"] == ["client@acme.com"]

# 3) an owner-bound report is not gated (no self-review loop)
sent.clear()
resend.Emails.send(report("jacob.starling@echoframe.net"))
results["owner-bound report is not gated"] = len(sent) == 1 and sent[0]["to"] == ["jacob.starling@echoframe.net"]

# 4) REVIEW_MODE=off → instant auto-send (the full-autonomy switch)
os.environ["REVIEW_MODE"] = "off"
sent.clear()
resend.Emails.send(report("client@acme.com"))
results["REVIEW_MODE=off sends straight to customer"] = len(sent) == 1 and sent[0]["to"] == ["client@acme.com"]
os.environ["REVIEW_MODE"] = "on"

print("\nReview-gate tests")
print("=" * 48)
ok = True
for name, passed in results.items():
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok = ok and passed
print("=" * 48)
print("ALL PASS ✓" if ok else "SOME FAILED ✗")
sys.exit(0 if ok else 1)
