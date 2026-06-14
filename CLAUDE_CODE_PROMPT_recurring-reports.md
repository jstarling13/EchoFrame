# Claude Code prompt — EchoFrame recurring monthly report automation

> Run Claude Code inside `01_Code/echoframe-backend/` (or the repo root) and paste everything in the box below.

---

CONTEXT
I run EchoFrame, a $150/month recurring "Monthly Clarity Report" service for Columbus small businesses. My marketing site is live at https://echoframe.net (a static site hosted on Vercel, project "echoframe-live"). This repo holds my backend.

- main.py — FastAPI app: Stripe webhook, secure file-upload routes (GET /upload, POST /api/upload, plus a 3-file /upload/revenue-suite), saves a customer sidecar JSON + the uploaded CSV to a local uploads/ folder.
- engine.py — generates the report (Claude via ANTHROPIC_API_KEY) and emails the finished report to the client via Resend (RESEND_API_KEY).
- intake_specs.py + templates/ — the per-product upload ("drop") pages; "clarity" asks the client to upload their monthly P&L.
- server.js — separate Node/Express app that only creates Stripe Checkout sessions; the Clarity Report is mode: 'subscription'.
- Env vars already in use: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, RESEND_API_KEY, CLIENT_URL.

MY DETAILS (use these)
- Owner / alert email (where I want "client hasn't uploaded" alerts sent): jacob.starling@echoframe.net
- Account/personal email (already on file): jacobstarling4313@gmail.com
- Client-facing "from" address for emails: use reports@echoframe.net (or jacob.starling@echoframe.net) — whichever is cleanest with Resend domain verification.
- Marketing site (live): https://echoframe.net
- The FastAPI backend will be deployed SEPARATELY on Vercel. The upload links I email to clients must point at the backend, not the static site. Use a configurable PUBLIC_BASE_URL env var. I plan to put the backend on a subdomain like https://app.echoframe.net (I'll add the DNS CNAME to it in IONOS after deploy) — but make the base URL configurable so it also works on the raw *.vercel.app URL.

THE PROBLEM
The webhook only handles `checkout.session.completed` (first signup) and relies on Stripe's post-checkout redirect to send the buyer to the upload page. Monthly renewals are silent automatic charges with no redirect, so months 2, 3, 4... never prompt the client and no report goes out. The backend also isn't deployed yet, so none of this runs in production.

GOAL — build the recurring monthly fulfillment loop and deploy it on Vercel:
Stripe monthly payment succeeds → email that client a secure personal upload link → they drop their files on the page → the API receives them, generates the report, and auto-emails it to the client. Plus a reminder + an alert to me (jacob.starling@echoframe.net) if a client hasn't uploaded within 4 days of being billed.

TASKS (core logic — host-agnostic)
1. Add a webhook handler for `invoice.payment_succeeded`. Act on renewals (billing_reason == "subscription_cycle"); do NOT double-send on the first invoice (subscription_create) which the existing checkout flow already covers. Resolve the client's email + name from the Stripe customer/invoice.
2. Generate a secure, signed, expiring upload link (HMAC-SHA256 over email + billing period + expiry using a new SIGNING_SECRET env var) — it must NOT depend on a checkout session_id. Build the link from PUBLIC_BASE_URL. Email it to the client via Resend with a clear "send me this month's numbers" message.
3. Update /api/upload to accept and validate that signed token (constant-time compare, check expiry) as an alternative to the existing Stripe-session check, so renewal uploads work while month-1 keeps working.
4. After a valid renewal upload, run the same engine.generate() → Resend path so the report auto-sends to the client.
5. Add a reminder / safety-net job: find clients billed this period who haven't uploaded within 4 days → resend the upload link to the client AND send an alert email to jacob.starling@echoframe.net. Track per-period upload state.

VERCEL HOSTING ADAPTATION
6. Add a Vercel Python serverless entrypoint (e.g. api/index.py) exposing the FastAPI app via ASGI.
7. Replace local uploads/ filesystem writes (customer sidecars + CSVs + per-period upload state) with Vercel Blob and/or Vercel KV — the local folder does not persist on serverless.
8. Replace the in-memory webhook idempotency store with Vercel KV (set-if-not-exists + TTL).
9. Handle the function time limit: if report generation can exceed it, offload generation to a background/queued function or cron rather than doing it inline; document the approach.
10. Add the reminder job as a Vercel Cron. Provide vercel.json (routing + cron) and requirements.txt.

CONSTRAINTS
- Do not break the existing first-signup flow or server.js checkout.
- I will set all secrets myself as Vercel env vars — never hardcode keys. Tell me exactly which env vars to add (including the new SIGNING_SECRET, PUBLIC_BASE_URL, and the alert/from email addresses if you make those configurable).
- Keep the existing file-validation/security and rate limiting.

DELIVERABLES
- The code changes, with tests where practical.
- A short summary of what changed and why.
- A step-by-step deploy guide covering:
  - Vercel project setup for the backend (separate from the marketing site) and the env vars to add.
  - Pointing app.echoframe.net (CNAME) at the backend, if I choose to use the subdomain.
  - Resend setup: verifying echoframe.net as a sending domain (the DKIM/SPF DNS records I must add at IONOS) so client emails don't land in spam, and which "from" address to use.
  - Stripe Dashboard webhook setup: the endpoint URL + which events to enable (checkout.session.completed AND invoice.payment_succeeded).
  - How to test renewals locally with the Stripe CLI (e.g. `stripe trigger invoice.payment_succeeded`).

Before you start, read main.py, engine.py, intake_specs.py, and server.js, and ask me any clarifying questions. Then propose a short plan and wait for my OK before making changes.
