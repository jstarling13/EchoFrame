"""
stripe_webhook.py — LEGACY / DEPRECATED
─────────────────────────────────────────────────────────────────────────────

⚠️  DO NOT USE THIS FILE IN PRODUCTION.

The active, hardened Stripe webhook handler lives in main.py at the route:
    POST /webhook/stripe

This file has been superseded and kept only for historical reference.
It contained the following security deficiencies (now documented):

  1. PII LEAK — logged customer_email and payment amount to stdout
  2. WRONG SIGNATURE — called generate_clarity_report(session_dict) but the
     function expects (email: str, name: str, industry: str, location: str)
  3. NO RATE LIMITING — no slowapi or express-rate-limit applied
  4. NO IDEMPOTENCY GUARD — duplicate Stripe retries would re-process events

The production webhook in main.py addresses all four issues.

─────────────────────────────────────────────────────────────────────────────
"""

# This module is intentionally left empty.
# See main.py → stripe_webhook() for the production implementation.
