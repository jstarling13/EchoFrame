# Vercel Preview readiness — confirmation and exact owner actions

**Status:** code is Preview-ready and verified below. No deployment was
attempted in this session (project creation is permission-blocked — see
"Owner action 1"). No live Stripe objects created. No IONOS DNS changed.
No Production deploy attempted.

This document answers the 11 specific Preview-readiness questions in
order, each with the code/evidence that backs it, then gives the exact
owner actions to actually stand up a Preview deployment.

## 1. Root Directory is `website`

Confirmed by repository layout: `website/package.json`,
`website/next.config.ts`, and the entire Next.js App Router tree
(`website/app/`) are the only place a Next.js build can run from in this
repo. Nothing else in the repository is part of the deployable app. Set
Vercel's **Root Directory** project setting to `website` — see Owner
action 2.

## 2. Exact Preview environment variables

Full table with Development/Production scoping is in
`website/docs/VERCEL_DEPLOYMENT.md`. The **Preview** column, condensed
and reflecting this task's specific requirements (Resend as the first
working lead destination, CRM optional):

| Variable | Preview value | Required? |
|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | leave unset (falls back to the Preview deployment's own origin) | No |
| `STRIPE_SECRET_KEY` | `sk_test_...` (test mode only — see §3) | Yes, before any checkout testing |
| `STRIPE_WEBHOOK_SECRET` | test-mode webhook signing secret | Yes, before webhook testing |
| `STRIPE_PRICE_O1`…`STRIPE_PRICE_O4`, `STRIPE_PRICE_O5_MONTHLY` | test-mode Price IDs (from `npm run stripe:sync`) | Yes, before checkout testing |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | `pk_test_...` | No (unused today — no Stripe.js on the client) |
| `RATE_LIMIT_STORE_URL` | Upstash Redis REST URL | **Yes — see §4** |
| `RATE_LIMIT_STORE_TOKEN` | Upstash Redis REST token | **Yes — see §4** |
| `EMAIL_PROVIDER_API_KEY` | Resend API key | **Yes — see §5** |
| `EMAIL_FROM` | a Resend-verified sending address | **Yes — see §5** |
| `LEAD_NOTIFICATION_EMAIL` | real inbox to receive lead notifications | **Yes — see §5** |
| `CRM_WEBHOOK_URL` | unset | No — see §6 |
| `CRM_WEBHOOK_SECRET` | unset | No |
| `PRIVACY_CONTACT_EMAIL` | optional | No |
| `ANALYTICS_ID` / `ERROR_MONITOR_DSN` | optional | No |
| `CONTACT_FORM_HONEYPOT_FIELD` | omit (defaults to `company_website`) | No |

## 3. Stripe test-mode keys are required in Preview

Enforced in code, not just documentation: `lib/stripe.ts`'s
`getStripeClient()` throws if `STRIPE_SECRET_KEY` starts with `sk_live_`
and `isProductionDeployment()` is false. `isProductionDeployment()`
(`lib/environment.ts`) checks `VERCEL_ENV === "production"` — on a
Preview deployment `VERCEL_ENV` is `"preview"`, so a live key throws
immediately rather than silently working. Covered by
`website/tests/api-stripe-checkout-route.test.ts` ("refuses a live-mode
key outside Production").

## 4. Durable rate-limit and webhook-idempotency storage is required

Enforced in code: `lib/durable-store.ts`'s `requireDurableStoreInProduction()`
and the checks in `lib/idempotency.ts`/`lib/rate-limit.ts` gate on
`NODE_ENV === "production"` — Vercel sets `NODE_ENV=production` for
**both** Preview and Production builds, so this applies to Preview too,
not just the eventual live site. Without `RATE_LIMIT_STORE_URL`/
`RATE_LIMIT_STORE_TOKEN` configured in Preview:

- Stripe webhook processing fails closed (`500`, Stripe retries) —
  `website/tests/idempotency.test.ts`.
- The contact form still works (fails open) but logs a loud
  `rate_limit_durable_store_missing_production` event every time —
  `website/tests/rate-limit.test.ts`.

Full explanation and required store type in `website/docs/DURABLE_STORE.md`.

## 5. Resend email as the first functioning lead destination

`lib/email.ts` already implements Resend's REST API directly (`POST
https://api.resend.com/emails`, bearer-token auth) — no SDK dependency,
already wired into the contact route. With `EMAIL_PROVIDER_API_KEY`,
`EMAIL_FROM`, and `LEAD_NOTIFICATION_EMAIL` set in Preview and
`CRM_WEBHOOK_URL` left unset, a submitted lead is emailed to
`LEAD_NOTIFICATION_EMAIL` and the endpoint returns success. This is
exactly the "one functioning lead destination" the production guard in
§6/`app/api/contact/route.ts` requires.

## 6. CRM may remain disabled if email delivery works

Enforced in code: `lib/lead-routing.ts`'s `resolveSubmissionOutcome()`
counts only *configured* destinations. With `CRM_WEBHOOK_URL` unset
(`crmConfigured: false`) and email configured and succeeding
(`emailConfigured: true, emailSent: true`), `configuredCount` is 1 and
`successCount` is 1 → outcome `"delivered"`, a normal 200 response. CRM
is optional, not required, as long as at least one destination is
configured and working. Covered by `website/tests/lead-routing.test.ts`
("email-only: succeeds when the one configured destination succeeds") and
`website/tests/api-contact-route.test.ts` ("email-only: succeeds").

## 7. Preview deployments are noindex/nofollow

`app/robots.ts` returns `disallow: "/"` for everything whenever
`isProductionDeployment()` is false (i.e. on Preview and local builds).
`app/layout.tsx`'s root metadata sets `robots: { index: false, follow:
false }` the same way. Verified via `website/tests/environment.test.ts`
and, previously, a live Lighthouse run (the `is-crawlable` audit
correctly failed on a non-production build, confirming the meta tag and
robots.txt both take effect).

## 8. Attorney-draft legal pages remain noindex and visibly labeled

`/privacy` and `/terms` set `robots: { index: false, follow: true }`
directly in their own page metadata — **unconditionally**, independent of
`isProductionDeployment()`, so they stay noindex even once the real
Production site is otherwise indexable. Both pages also render a visible
on-page callout ("Draft for attorney review... not yet approved by
counsel...") in addition to the site-wide `DraftBanner` shown on every
page. Neither the noindex meta tag nor the visible callout depends on any
environment variable — they cannot be accidentally left off.

## 9. No live Stripe key can be used accidentally in Preview

Same mechanism as §3 — this isn't just "don't paste a live key into
Preview," it's enforced so that even if one were pasted in by mistake,
every Stripe-backed route (`checkout`, `webhook`) throws before
constructing a Stripe client with it. Confirmed via
`website/tests/api-stripe-checkout-route.test.ts` ("refuses a live-mode
key outside Production (fails closed, returns 502, not a live charge)").

## 10. No IONOS or production-domain work is required for Preview

Every Vercel Preview deployment gets an automatic `*.vercel.app` URL the
moment it deploys — no custom domain, no DNS record, and therefore no
IONOS access or changes of any kind are needed to stand up or review a
Preview. Domain/DNS work (`website/docs/IONOS_DNS_PLAN.md`) is entirely a
Production-launch concern and stays untouched by everything in this
document.

## 11. Test results

All local checks re-run and passing as of this document:

| Check | Result |
|---|---|
| `tsc --noEmit` | Pass, 0 errors |
| `eslint .` | Pass, 0 errors/warnings |
| `vitest run` | Pass, 70/70 across 9 files |
| `next build` | Pass, 25 routes (24 app routes + `/icon.png`), 0 warnings |

---

## Exact owner actions

### A. Fix the Vercel project-creation permission

In the Vercel dashboard, open **Team Settings → Members** for
`EchoFrame's projects` (`team_aRAPqQAKxNgEEADhOrrt1byO`). Find the
member/integration this AI session's Vercel connector authenticates as,
and confirm its role includes **project creation** — Vercel's built-in
"Member" role can create projects; "Viewer" and some restricted custom
roles cannot. (Reference: https://vercel.com/docs/accounts/team-members-and-roles.)
Without this, no project can be created by this integration, by direct
file upload or by Git import.

### B. Create/import the Vercel project

This repository has **no Git remote** yet (local-only). Two ways to
proceed:

- **Recommended:** push this repo to GitHub/GitLab/Bitbucket (a separate
  explicit action — confirm before doing this), then in Vercel: **Add
  New → Project**, import that repository, and set:
  - **Root Directory:** `website`
  - **Framework Preset:** Next.js (auto-detected)
  - **Build Command:** `next build` (default)
  - **Install Command:** `npm install` (default)
- **Alternative:** once permission is fixed (Action A), a direct-file
  Preview deployment can be retried without a Git remote at all.

### C. Configure Preview environment variables

In **Project Settings → Environment Variables**, scope every variable in
the §2 table above to **Preview** (not Production, not "all
environments"). Do this before the first deploy so the build has what it
needs.

### D. Create Stripe test objects

Run, yourself, with your own Stripe **test-mode** secret key — never
paste this key into chat or hand it to an AI session:

```bash
STRIPE_SECRET_KEY=sk_test_xxx npm run stripe:sync
```

(from the `website/` directory). This creates one Stripe Product + Price
per offer (O1–O5) in test mode and prints the exact `STRIPE_PRICE_*`
values to paste into the Preview environment variables from step C. It
also prints the O2–O4 invoice-only milestone amounts for reference — no
public Price is created for those, they're billed later by hand via
Stripe Invoices.

### E. Configure durable storage

Provision an Upstash Redis database (or any Redis REST-compatible
equivalent) and set `RATE_LIMIT_STORE_URL` / `RATE_LIMIT_STORE_TOKEN` in
Preview per step C. Full rationale in `website/docs/DURABLE_STORE.md`.

### F. Configure Resend

Create a Resend account (or use an existing one), verify a sending
domain/address, generate an API key, and set `EMAIL_PROVIDER_API_KEY`,
`EMAIL_FROM` (the verified address), and `LEAD_NOTIFICATION_EMAIL` (where
leads should land) in Preview per step C. Leave `CRM_WEBHOOK_URL` unset —
per §6, email alone is sufficient for the contact form to work correctly
in Preview.

### G. Deploy and review the Preview

1. Trigger the deploy (push to the connected branch, or redeploy from the
   Vercel dashboard).
2. Confirm `robots.txt` on the Preview URL disallows everything and the
   homepage `<head>` has `<meta name="robots" content="noindex, nofollow">`.
3. Confirm `/privacy` and `/terms` show the attorney-review callout and
   are noindex.
4. Submit the `/contact` form once and confirm the lead email arrives at
   `LEAD_NOTIFICATION_EMAIL` via Resend.
5. There is no public "pay now" button in the UI yet — the site's only
   current CTA is "Book a fit call" to `/contact`, by design (see
   `WEBSITE_SPECIFICATION.md`). To verify the checkout route itself
   works, call it directly: `curl -i -X POST
   https://<preview-url>/api/stripe/checkout -H "Content-Type:
   application/json" -d '{"offerCode":"O1"}'` and confirm the `303`
   redirect `Location` header points at `checkout.stripe.com` with a
   test-mode session — never a live charge.
6. Only after this review passes does it make sense to talk about
   Production, a real domain, or live Stripe keys — none of that is part
   of this Preview task.
