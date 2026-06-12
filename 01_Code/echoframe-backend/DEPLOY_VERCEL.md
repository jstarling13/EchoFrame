# EchoFrame backend — Vercel deploy & recurring-renewal guide

This backend (FastAPI) is deployed **separately** from the marketing site
(`echoframe-live`). It handles secure uploads, the Stripe webhook, report
generation, and the monthly recurring-fulfilment loop.

---

## 0. What changed (summary)

The webhook only handled `checkout.session.completed` (first signup). Monthly
renewals are silent automatic charges with no redirect, so months 2, 3, 4…
never prompted the client. This adds the recurring loop and makes it deploy on
Vercel serverless:

| Area | Change |
|------|--------|
| **Renewal webhook** | New `invoice.payment_succeeded` handler. Acts only on `billing_reason == "subscription_cycle"` (never double-sends on the first `subscription_create` invoice). Resolves the client's email/name and routes the Stripe product → report via the existing `route_stripe_purchase()`. |
| **Signed links** | `sign.py` — HMAC-SHA256 over `email\|product\|tier\|period\|exp` with `SIGNING_SECRET`. No `session_id` dependency. `/api/upload` accepts a valid token (constant-time compare + expiry) as an alternative to the month-1 Stripe-session check. |
| **Auto-send** | A valid renewal upload runs the same `engine.generate()` → Resend path, so the report auto-emails to the client. |
| **Reminder safety-net** | `reminders.py` + a daily Vercel Cron at `/api/cron/reminders`: any client billed > 4 days ago who hasn't uploaded gets the link re-sent **and** an alert goes to `jacob.starling@echoframe.net`. Per-period state prevents repeat nags. |
| **Serverless storage** | `store.py` — durable state (customer directory, per-period upload state, webhook idempotency) in **Upstash Redis**; in-memory fallback for local dev. Uploaded CSVs + generated reports are transient in `/tmp` (`ECHOFRAME_UPLOADS_DIR` / `ECHOFRAME_REPORTS_DIR`, honoured by all 16 report engines). |
| **Idempotency** | Redis `SET NX EX` replaces the in-memory dict in production (in-memory kept as fallback). |
| **Generation** | Runs **inline** on Vercel (background tasks aren't guaranteed to run after a serverless response). `maxDuration: 300` covers the Claude call. |
| **Entrypoint** | `api/index.py` exposes the FastAPI app via ASGI; `vercel.json` provides routing + cron + bundling. |

**Untouched:** `server.js` checkout, the month-1 signup flow, all file
validation / rate limiting / security headers, and every report engine's bundled
sample/template/logo assets (only the upload/report *write* paths were redirected).

---

## 1. Environment variables (set these in Vercel → Project → Settings → Env Vars)

Never hardcode keys. Set all of these on the **backend** project:

**Already in use (copy from your current setup):**
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`  ← use the signing secret of the **new** endpoint (step 5)
- `ANTHROPIC_API_KEY`
- `RESEND_API_KEY`

**New — required for the renewal loop:**
- `SIGNING_SECRET` — generate once: `openssl rand -hex 32`
- `PUBLIC_BASE_URL` — where upload links point. `https://app.echoframe.net`
  once the CNAME is live, or the raw `https://<project>.vercel.app` until then.
- `EMAIL_FROM` — `EchoFrame <jacob.starling@echoframe.net>`
- `ALERT_EMAIL` — `jacob.starling@echoframe.net`
- `CRON_SECRET` — `openssl rand -hex 32` (Vercel sends it to the cron as a Bearer token)

**Durable store (Upstash Redis):** add the **Upstash** integration from the
Vercel Marketplace and attach it to this project — it auto-injects
`KV_REST_API_URL` and `KV_REST_API_TOKEN`. Without these the app runs on a
non-durable in-memory fallback (fine locally, **not** for production — idempotency
and reminder state won't survive between serverless invocations).

> Optional: `REMINDER_AFTER_DAYS` (default 4). `ECHOFRAME_UPLOADS_DIR` /
> `ECHOFRAME_REPORTS_DIR` default to `/tmp/echoframe/...` via `api/index.py` —
> leave unset.

---

## 2. Create the Vercel project (backend)

1. New Project → import this repo → set **Root Directory** to
   `01_Code/echoframe-backend`.
2. Framework preset: **Other**. Vercel detects `vercel.json` + `requirements.txt`.
3. Add all env vars from step 1, then **Deploy**.
4. Confirm it boots: visit `https://<project>.vercel.app/upload` — you should see
   the upload page.

> **Plan note:** `maxDuration: 300` in `vercel.json` requires **Vercel Pro**
> (Hobby caps functions at 60 s and crons at once-per-day). On Hobby, lower
> `maxDuration` to `60`; a single Claude call usually fits but is tighter.
>
> **Bundle size:** the report engines pull in `pandas` + `matplotlib`, which are
> large. If a deploy fails on the 250 MB unzipped limit, move `pytest*` out of
> `requirements.txt` (not needed in prod) and consider a lighter chart path.

---

## 3. Point `app.echoframe.net` at the backend (optional subdomain)

1. Vercel → backend project → **Settings → Domains** → add `app.echoframe.net`.
2. In **IONOS** DNS for `echoframe.net`, add the record Vercel shows — typically:
   - **CNAME** `app` → `cname.vercel-dns.com`
3. Wait for it to verify, then set `PUBLIC_BASE_URL=https://app.echoframe.net`
   and redeploy (or just update the env var and redeploy).

Until the CNAME is live, set `PUBLIC_BASE_URL` to the `*.vercel.app` URL — the
signed links work either way.

---

## 4. Resend — verify `echoframe.net` as a sending domain

So renewal/report emails don't land in spam:

1. Resend → **Domains → Add Domain** → `echoframe.net`.
2. Resend shows DNS records. In **IONOS** add them on `echoframe.net`:
   - **DKIM** — a `CNAME` (or `TXT`) record, e.g. host `resend._domainkey` → the
     value Resend gives.
   - **SPF** — a `TXT` on the sending subdomain (Resend uses `send.echoframe.net`):
     `v=spf1 include:amazonses.com ~all` (use exactly what Resend shows).
   - **MX** — on `send` → `feedback-smtp.<region>.amazonses.com` (priority 10).
   - Optional **DMARC** — `TXT` at `_dmarc` → `v=DMARC1; p=none;`.
3. Click **Verify** in Resend until all records are green.
4. **From address:** `EMAIL_FROM=EchoFrame <jacob.starling@echoframe.net>`
   (already your `ALERT_EMAIL` too). Replies land with you directly.

---

## 5. Stripe Dashboard — webhook endpoint

1. Stripe → **Developers → Webhooks → Add endpoint**.
2. **Endpoint URL:** `https://app.echoframe.net/webhook/stripe`
   (or the `*.vercel.app` URL).
3. **Events to send** — enable both:
   - `checkout.session.completed`  (month-1 signup — existing)
   - `invoice.payment_succeeded`   (monthly renewals — new)
4. Save, copy the endpoint's **Signing secret** (`whsec_…`) into Vercel as
   `STRIPE_WEBHOOK_SECRET`, and redeploy.

---

## 6. Test renewals locally with the Stripe CLI

```bash
# from 01_Code/echoframe-backend, with .env populated (incl. SIGNING_SECRET, PUBLIC_BASE_URL)
uvicorn main:app --reload --port 8000

# in another terminal:
stripe login
stripe listen --forward-to localhost:8000/webhook/stripe
# copy the whsec_… it prints into your .env as STRIPE_WEBHOOK_SECRET, restart uvicorn

# fire a renewal:
stripe trigger invoice.payment_succeeded
```

The default `stripe trigger` invoice has `billing_reason: "manual"`, so the
handler will **correctly skip it** (logs `Invoice ignored`). To exercise the real
path, either:
- use a `--override` to set `billing_reason=subscription_cycle` and a known
  `lines.data[0].price.product`, or
- create a real test-mode subscription with a short interval and let it renew, or
- run the unit tests, which simulate the exact event:
  `pytest tests/test_renewals.py -v`.

Then visit the link from the logged/emailed URL, drop a CSV, and confirm the
report email arrives.

### Test the reminder cron
```bash
curl -H "Authorization: Bearer $CRON_SECRET" https://app.echoframe.net/api/cron/reminders
```
Returns a JSON summary (`checked` / `reminded` / `already` / `errors`).

---

## 7. Run the test suite

```bash
pytest -q          # 97 tests: existing security + new renewal coverage
```
