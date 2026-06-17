"""
EchoFrame — LIVE end-to-end test of the human-review gate.
Run on your Mac:   python3 test_review_live.py

What it does (with REAL emails through your verified echoframe.net domain):
  1. Generates a sample report addressed to a test "customer".
  2. The review gate HOLDS it and emails YOU a review copy (Approve / Hold +
     the report attached). The customer gets nothing yet.
  3. The script then does what clicking "Approve & send" does — releases the
     report to the customer.

Both emails land in your inbox (the customer is a +alias of your Gmail), so you
can see the whole flow. Uses the live RESEND_API_KEY from .env.
"""
import os, sys, time, base64
from pathlib import Path

# Load .env (live Resend key) — no dependency on python-dotenv ----------------
ENV_PATH = Path(__file__).resolve().parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except Exception:
    pass
# Robust manual fallback: parse KEY=VALUE lines for anything still missing.
if ENV_PATH.exists():
    for _line in ENV_PATH.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

if not os.environ.get("RESEND_API_KEY"):
    sys.exit(f"RESEND_API_KEY not found. Looked in: {ENV_PATH}")

# Test config ----------------------------------------------------------------
OWNER_INBOX   = "jacobstarling4313@gmail.com"               # where the review copy goes
TEST_CUSTOMER = "jacobstarling4313+testcustomer@gmail.com"  # non-owner → gate fires; still your inbox

os.environ["REVIEW_MODE"]     = "on"
os.environ["ALERT_EMAIL"]     = OWNER_INBOX
os.environ["FAILSAFE_EMAIL"]  = OWNER_INBOX
os.environ.setdefault("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")
os.environ.setdefault("PUBLIC_BASE_URL", "https://echoframe-production.up.railway.app")

try:
    import resend
except ImportError:
    sys.exit("The 'resend' package isn't installed. Run:  pip3 install resend python-dotenv")

resend.api_key = os.environ["RESEND_API_KEY"]

import email_failsafe
import review_gate
email_failsafe.install()
review_gate.install()

# A small, realistic sample report to attach ---------------------------------
report_html = """<!doctype html><html><body style="font:15px system-ui;color:#0a274f;max-width:640px;margin:auto">
<h1 style="color:#0a274f">EchoFrame — Monthly Clarity Report</h1>
<p style="color:#6b7280">The Copper Skillet · May 2026 · prepared for the owner</p>
<h3>The one thing to fix this month</h3>
<p>Food cost ran 34.1% of sales in May vs. your 29% target — roughly <strong>$3,900</strong>
left on the table, almost all of it in protein waste on the weekend dinner shift.</p>
<p style="color:#c9973d"><strong>Move:</strong> tighten weekend protein par levels to last month's
actual covers; recheck next month's report to confirm the gap closes.</p>
<p style="color:#9ca3af;font-size:12px">Business intelligence, not accounting software. Informational only.</p>
</body></html>"""
attachment = base64.b64encode(report_html.encode()).decode()

report_email = {
    "from": os.environ["EMAIL_FROM"],
    "to": [TEST_CUSTOMER],
    "subject": "Your May 2026 Clarity Report — The Copper Skillet",
    "html": "<p>Hi there,</p><p>Your May 2026 Monthly Clarity Report is attached. "
            "The headline: one specific, dollar-tied fix worth about $3,900 this month.</p><p>— EchoFrame</p>",
    "attachments": [{"filename": "EchoFrame_Clarity_May2026.html",
                     "content": attachment, "content_type": "text/html"}],
}

print("\n" + "=" * 64)
print("EchoFrame review-gate LIVE test")
print("=" * 64)
print(f"  Sender (verified):  {report_email['from']}")
print(f"  Test customer:      {TEST_CUSTOMER}")
print(f"  Your review inbox:  {OWNER_INBOX}")
print("-" * 64)

# Step 1 — engine "sends" the report; the gate holds it ----------------------
print("1) Generating report and handing it to delivery...")
result = resend.Emails.send(report_email)
held_id = str(result.get("id", "")).replace("review-held-", "") if isinstance(result, dict) else ""
if not held_id or not str(result.get("id", "")).startswith("review-held-"):
    sys.exit(f"   ✗ Expected the gate to HOLD the report, got: {result}")
print(f"   ✓ HELD — customer received NOTHING. Review copy emailed to {OWNER_INBOX}.")
print(f"     (review id: {held_id})")
print("     → Check your inbox now: '[REVIEW] ... → {}' with Approve/Hold + the report attached."
      .format(TEST_CUSTOMER))

# Step 2 — approve (exactly what clicking 'Approve & send' does) --------------
print("\n2) Approving in 4s (this is what the email's 'Approve & send' button calls)...")
time.sleep(4)
review_gate.release(held_id)
print(f"   ✓ APPROVED — report delivered to the customer ({TEST_CUSTOMER}).")

print("\n" + "=" * 64)
print("Done. Two emails should arrive in your inbox:")
print("  • [REVIEW] ...  — the held report awaiting your approval")
print("  • Your May 2026 Clarity Report — the released customer copy")
print("See both in Resend → Emails:  https://resend.com/emails")
print("=" * 64 + "\n")
