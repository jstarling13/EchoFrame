# EchoFrame Security Guide

## ⚠️ IMMEDIATE ACTION REQUIRED — Key Rotation

A security audit (2026-05-30) found that production API keys were stored in
plaintext `.txt` files inside this directory, which is synced to OneDrive.
**All exposed keys must be rotated immediately.**

### Keys to Rotate

| Service    | Where to rotate                                   | .env variable              |
|------------|---------------------------------------------------|----------------------------|
| Stripe     | https://dashboard.stripe.com/apikeys              | `STRIPE_SECRET_KEY`        |
| Stripe     | https://dashboard.stripe.com/apikeys              | `STRIPE_PUBLISHABLE_KEY`   |
| Stripe     | https://dashboard.stripe.com/webhooks             | `STRIPE_WEBHOOK_SECRET`    |
| Anthropic  | https://console.anthropic.com/settings/keys       | `ANTHROPIC_API_KEY`        |
| Resend     | https://resend.com/api-keys                       | `RESEND_API_KEY`           |

### After rotating, update `.env` with the new values only.

---

## Secret Storage Rules

1. **`.env` is the only place for secrets.** It is in `.gitignore` — do not
   remove it from `.gitignore`.
2. **Never paste secrets into `.txt` files.** They can't be gitignored reliably
   and will be cloud-synced.
3. **Never hardcode keys in source files** (`server.js`, `main.py`, etc.).
4. In production (Heroku, Railway, Render, etc.) use the platform's environment
   variable dashboard — not a `.env` file on the server.

---

## Security Controls Summary

### Authentication & Authorization
- Every `/api/upload` request is verified against a **live Stripe Checkout
  Session**. The session email must match the submitted email (BOLA protection).
- No upload is accepted without a completed, valid payment.

### Input Validation
- Email validated via strict regex allowlist before any processing.
- File path traversal prevented — email is passed through `_safe_email()` which
  converts to an alphanumeric+`_-` stem before use as a filename.
- File extension, content-type, size (5 MB max), and UTF-8 encoding all checked.

### Webhook Security
- Stripe webhook signature verified via `stripe.Webhook.construct_event()`.
- Timestamp tolerance enforced (Stripe default: 300 seconds) — replay attacks
  with stale signatures are rejected.
- In-memory idempotency guard prevents duplicate event processing.

### LLM Hardening
- User-supplied data is **sanitized** (control chars stripped, length capped)
  before being placed in the user message.
- The **system prompt contains zero user data** — it is entirely static.
- System prompt explicitly instructs the model to ignore override attempts.
- LLM output validated before entering the document builder (`_validate_llm_output`).
- XML/HTML tags stripped from all LLM string output.

### HTTP Security Headers (all responses)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Strict-Transport-Security` (HTTPS only)
- Full Helmet.js CSP on the Node server

### Rate Limiting
- `/api/upload`: 5 requests / minute per IP
- `/webhook/stripe`: 60 requests / minute per IP
- `/create-checkout-session`: 10 requests / minute per IP

---

## Running the Security Test Suite

```bash
cd echoframe-backend
pip install -r requirements.txt
pytest tests/test_security.py -v
```

Tests are designed to **FAIL** if a security control is removed. Run them
before every deployment.

---

## Known Limitations (for future hardening)

- `_processed_webhook_events` is an in-memory set — restarting the server
  resets it. Replace with Redis or a DB table for production resilience.
- No persistent user authentication layer — access is gated by payment only.
  Acceptable for a pay-per-report model; add JWT sessions if accounts are added.
- CORS `CLIENT_URL` should list only the production domain in `.env` for
  production deployments (not `localhost`).
