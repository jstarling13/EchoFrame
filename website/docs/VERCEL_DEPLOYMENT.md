# Vercel deployment

**Status:** not connected. No Vercel project exists yet. This document is
the exact, ready-to-execute owner plan — this audit did **not** attempt
another deployment (per instruction: "Do not attempt another deployment
until the permission issue is resolved").

## Prior attempt and the blocker

With the owner's approval in an earlier session, a direct-file Preview
deployment was attempted via a Vercel MCP connector to team `EchoFrame's
projects` (`team_aRAPqQAKxNgEEADhOrrt1byO`), project name
`practical-ai-operations`. Both attempts (explicit team ID, and none)
failed identically:

```
Vercel API error 403: {"error":{"code":"forbidden","message":"You don't have
permission to create a project.","action":"View Documentation",
"link":"https://vercel.com/docs/accounts/team-members-and-roles"}}
```

This is a role/permission limit on the connected Vercel account/integration
— not a code or repository problem. The repo builds cleanly (see
`IMPLEMENTATION_REPORT.md` and this audit's QA results). Pick **one** of
the two paths below to unblock it.

## Path A — grant the connected integration permission to create a project

1. In the Vercel dashboard, open **Team Settings > Members** for
   `EchoFrame's projects` (`team_aRAPqQAKxNgEEADhOrrt1byO`).
2. Find whatever member/integration/token this session's Vercel connector
   authenticates as, and confirm its role includes **project creation**
   (Vercel's built-in "Member" role can create projects; "Viewer" or
   certain restricted/custom roles cannot — see
   https://vercel.com/docs/accounts/team-members-and-roles).
3. Once elevated, a future session can retry the direct-file Preview
   deployment, or proceed to connect a real Git remote (Path B is
   preferred once a GitHub/GitLab/Bitbucket remote exists, since it gives
   auto-deploy-on-push instead of one-off file uploads).

## Path B — create the project manually and connect this repository

This repo currently has **no Git remote** (it's local-only). To connect it
to Vercel the standard way:

1. Push this repository to GitHub (or GitLab/Bitbucket) under whatever
   account/org will own it. (This is a separate explicit action — ask
   before creating/pushing to a remote if that hasn't been approved yet.)
2. In the Vercel dashboard: **Add New... > Project**, import that Git
   repository.
3. Configure the project:
   - **Root Directory:** `website` (this repo is not a monorepo tool
     setup — just point Vercel at the `website/` subfolder as the project
     root; everything Vercel needs, including `package.json`, lives
     there).
   - **Framework Preset:** Next.js (auto-detected once Root Directory is
     set correctly).
   - **Build Command:** `next build` (default — no override needed).
   - **Install Command:** `npm install` (default).
   - **Output:** managed automatically by the Next.js framework preset;
     no manual output directory setting needed.
4. Add environment variables (exact list below) before the first deploy.
5. Deploy. The first deploy from the default/production branch becomes
   the Production deployment; every other branch/PR becomes a Preview
   deployment automatically from then on.

## Environment variables — exact scoping

Set these in **Project Settings > Environment Variables**. Vercel lets you
tick which of Development / Preview / Production each variable applies to
— use the table below, not "all environments" for everything.

| Variable | Development | Preview | Production | Secret? |
|---|---|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | Preview deployment URL (Vercel provides one per deploy; can leave unset and it'll fall back to the request origin) | Final production domain | No |
| `LEAD_NOTIFICATION_EMAIL` | optional | recommended (real inbox to verify lead delivery) | required | No |
| `PRIVACY_CONTACT_EMAIL` | optional | optional | required (once real) | No |
| `CRM_WEBHOOK_URL` | optional | recommended | required (or `EMAIL_*` must be set — production needs at least one, see `app/api/contact/route.ts`) | No (URL only) |
| `CRM_WEBHOOK_SECRET` | optional | if `CRM_WEBHOOK_URL` set | if `CRM_WEBHOOK_URL` set | **Yes** |
| `STRIPE_SECRET_KEY` | `sk_test_...` only | **`sk_test_...` only — never live** | `sk_live_...` (only after the full test matrix passes and owner approves) | **Yes** |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | test `pk_test_...` (unused today — no Stripe.js on the client, kept for future) | `pk_test_...` | `pk_live_...` | No (publishable by design, but still don't cross-wire test/live) |
| `STRIPE_WEBHOOK_SECRET` | test webhook signing secret | **test webhook signing secret** | live webhook signing secret | **Yes** |
| `STRIPE_PRICE_O1` .. `STRIPE_PRICE_O4`, `STRIPE_PRICE_O5_MONTHLY` | test-mode Price IDs | **test-mode Price IDs** | live-mode Price IDs | No (IDs, not secrets, but test/live must not cross) |
| `EMAIL_PROVIDER_API_KEY` | optional | recommended | required (or `CRM_WEBHOOK_URL` must be set) | **Yes** |
| `EMAIL_FROM` | optional | if email configured | if email configured | No |
| `ANALYTICS_ID` | unset | optional | optional | No |
| `ERROR_MONITOR_DSN` | unset | recommended | recommended | Treat as secret-ish (don't need strict secrecy, but don't need it public either) |
| `RATE_LIMIT_STORE_URL` | unset (uses in-memory fallback locally — allowed, see `website/docs/DURABLE_STORE.md`) | **required** (Preview counts as non-dev per the durable-store guard's `NODE_ENV` check) | **required** | No (URL) |
| `RATE_LIMIT_STORE_TOKEN` | unset | **required** | **required** | **Yes** |
| `CONTACT_FORM_HONEYPOT_FIELD` | `company_website` (default, can omit) | same | same | No |

**Bold** = the specific items this audit's guards actively enforce:
`STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`/`STRIPE_PRICE_*` must be
test-mode in Preview (`lib/stripe.ts` throws if a `sk_live_` key is used
outside `VERCEL_ENV=production`); `RATE_LIMIT_STORE_URL`/`_TOKEN` must be
set in both Preview and Production or Stripe webhook processing fails
closed (`lib/idempotency.ts`) and the contact form loudly flags degraded
rate limiting (`lib/rate-limit.ts`).

## Verifying after deploy

1. Confirm the Preview URL's `robots.txt` disallows everything and the
   homepage has `<meta name="robots" content="noindex, nofollow">` — this
   should happen automatically (`app/robots.ts`, `app/layout.tsx` gate on
   `VERCEL_ENV === "production"`). If it doesn't, something is
   misconfigured.
2. Confirm `/privacy` and `/terms` are `noindex` even once Production is
   live (they carry their own explicit `robots: { index: false }`,
   independent of environment — they're attorney-review drafts).
3. Run the acceptance checklist in
   `archive/original_claude_implementation_brief/ACCEPTANCE_CRITERIA.md`
   and `TEST_PLAN.md` against the Preview URL.
4. Run `npm run stripe:sync` yourself (with your own `sk_test_` key —
   never share it with an AI session) to create the test-mode Stripe
   products/prices, then paste the printed Price IDs into the Preview
   environment variables.
5. Only after the owner reviews a healthy Preview: promote to Production,
   configure the domain (`website/docs/IONOS_DNS_PLAN.md`), and only then
   consider live Stripe keys.

## Why no deployment was attempted in this audit

Per this audit's explicit instructions: "Do not attempt another
deployment until the permission issue is resolved." This document is the
complete, ready-to-execute plan for whoever resolves Path A or B next.
