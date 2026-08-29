# Pre-Merge Promotion Audit — White Oak Operations Website

**Date:** 2026-08-29 | **Branch:** `website-implementation` (not merged to `main`)
**Scope:** `website/lib/offers.ts`, Stripe payment architecture, O5 term
enforcement, durable-storage guards, lead-routing failure handling,
Preview safety, repository hygiene, legal governing-law language,
automated QA, Vercel deployment plan.

No merge to `main`. No live Stripe objects created. No IONOS DNS changed.
No Production deploy attempted.

## 1. Promotion classification

**PREVIEW-READY (code) — deployment execution BLOCKED on Vercel account permissions.**

The code itself passes every local check (typecheck, lint, 70 automated
tests, clean production build, 0 axe-core accessibility violations, 0
Lighthouse console errors, Lighthouse Performance/Accessibility 100) and
has no known outstanding defects. It is **not PRODUCTION-READY**: the
business/legal facts on `/about`, `/privacy`, and `/terms` are still
placeholders pending owner/counsel decisions, and no Stripe account (test
or live) has been connected to create real payment objects yet.

## 2. Critical defects found and fixed

1. **Stripe would have charged the full contract price instead of the
   deposit for O2, O3, and O4.** `lib/offers.ts` conflated "total contract
   value" with "amount to charge at checkout" in one field. Fixed by
   splitting into `totalUsd` + `milestones[]`, with exactly one
   `"checkout"` milestone per offer and the rest `"invoice"`-only
   (never a public Price or button). Regression-tested for every offer.
2. **Black text on a black background** on the "Book a fit call" button
   inside both the desktop and mobile nav — found via an axe-core scan,
   not visual review. A CSS specificity conflict from the Goldman-palette
   redesign (`.primary-nav a` beat `.btn-primary`). Fixed, verified 0
   violations before/after.
3. **CSP was blocking Next.js's own inline hydration scripts**, producing
   a real console/hydration error (found via Lighthouse, not just a lint
   warning). Tried a nonce-based CSP via middleware first; reverted after
   confirming it would force every route off static generation in this
   Next.js version. Kept `'unsafe-inline'` on `script-src` (matching the
   existing `style-src` treatment) as the documented, deliberate
   trade-off for a static site with no user-generated-HTML sink.
4. **Contact endpoint always returned 200, even when both CRM and email
   delivery were unconfigured or failed** — a lead could silently vanish.
   Now returns 503 in production when nothing was actually delivered.
5. **Stripe webhook idempotency relied on in-memory state**, unsafe across
   serverless instances. Now fails closed (500, Stripe retries) in
   production without a durable store configured or reachable.

## 3. Files changed / commits created (9, all on `website-implementation`)

| Commit | Summary |
|---|---|
| `6830462` | Stripe payment architecture fix (offers.ts, checkout route, sync script, catalog files, tests) |
| `7c66e7f` | O5 initial-term enforcement (subscription-term.ts, webhook, support page, docs) |
| `583ebb3` | Durable-store fail-closed guards (durable-store.ts, idempotency.ts, rate-limit.ts, docs, tests) |
| `f6e3aa4` | Lead-routing outcome model (lead-routing.ts, contact route, tests) |
| `6373dfa` | Preview noindex, live-key guard, black-on-black CSS fix, CSP decision |
| `1baed6a` | API route integration tests (contact + checkout) |
| `11294f1` | Preserve unique `_source_package` content (hygiene) |
| `783adb9` | Broaden governing-law language beyond NY-only assumption |
| `b7f4db0` | Exact Vercel connection plan documentation |

## 4. Exact payment table after corrections

| Offer | Total | Due at checkout (Stripe Price) | Invoiced later (SOW-based, no public Price) |
|---|---:|---:|---|
| O1 | $2,500 | $2,500 (full, before kickoff) | — |
| O2 | $7,500 | $3,750 (deposit, before kickoff) | $3,750 before production launch |
| O3 | $18,000 | $7,200 (deposit, before kickoff) | $5,400 after blueprint approval; $5,400 before launch |
| O4 | $45,000 | $13,500 (deposit, at kickoff) | $11,250 after blueprint approval; $11,250 after implementation acceptance; $9,000 before final handoff |
| O5 | — (ongoing) | $2,500/month, in advance | 3-month initial term = $7,500 minimum, contract-enforced (see `website/docs/O5_INITIAL_TERM.md`) |

Locked in by `website/tests/offers.test.ts` ("payment architecture — exact
amounts charged at checkout" suite).

## 5. Test results

| Check | Result |
|---|---|
| `npm install` | 390 packages, 0 vulnerabilities |
| `tsc --noEmit` | Pass, 0 errors |
| `eslint .` | Pass, 0 errors/warnings |
| `vitest run` | **Pass, 70/70** across 9 files (offers/payment, subscription-term, idempotency, rate-limit, lead-routing, environment, 2 API-route integration suites, validation) |
| `next build` | Pass, 24 routes, 0 warnings |
| `npm audit` | 0 vulnerabilities |
| Secret scan | 0 findings across all tracked files (patterns for Stripe/AWS/GitHub/Slack keys, private key blocks, generic secret assignments) |
| `.env` tracking check | Only `.env.example` tracked; `.gitignore` covers the rest |

## 6. Accessibility / Lighthouse results

axe-core 4.10.2 run against `/`, `/services`, `/contact`,
`/workflow-diagnostic`, `/support`, `/privacy` (local production build,
`npm run build && npm start`): **0 violations** on every page (after
fixing the black-on-black nav button). Some "incomplete" (needs-manual-
verification, not failure) contrast results on `/` were investigated and
confirmed to be axe environment/timing artifacts, not real defects —
spot-checked computed styles directly and found genuinely strong contrast
(white-on-black, ~21:1) on every flagged element.

Lighthouse (local production build, homepage): **Performance 100,
Accessibility 100, Best Practices 96, SEO 63.** The SEO score is
artificially low here because this build correctly sets `noindex` (no
`VERCEL_ENV=production`, per the Preview-safety fix) — it will resolve on
the real Production deployment where that variable is set. Remaining
minor, non-blocking items: `favicon.ico` returns 404 (deferred — see §9),
some unused-JS/render-blocking nitpicks typical of any Next.js app.

## 7. Repository hygiene recommendation

`_source_package/` is 1.1MB tracked; 97 of its 116 files (749KB) are
byte-identical duplicates of files already organized elsewhere in the
repo. The 19 genuinely-unique files have been copied (not moved) into
`archive/original_stripe_package/`, `archive/original_claude_implementation_brief/`,
and `website/docs/SOURCE_WEBSITE_*.md`. The original ZIP at
`/Users/jacob/Downloads/AI_CONSULTING_BUSINESS_BUILD_v1.zip` is confirmed
untouched (same size/timestamp/MD5 as before this session).

**Recommendation (not executed — needs your explicit approval):** once
you've reviewed the preserved copies, remove `_source_package/` from Git
tracking (`git rm -r --cached _source_package && git commit`). The ZIP +
the preserved files + the already-organized structure capture everything
of lasting value; keeping a full redundant extraction in Git forever adds
no information, just repo weight.

## 8. Exact Vercel owner steps

Full detail in `website/docs/VERCEL_DEPLOYMENT.md`. Two paths, pick one:

- **Path A:** grant the connected Vercel integration's role
  project-creation permission on team `EchoFrame's projects`
  (`team_aRAPqQAKxNgEEADhOrrt1byO`).
- **Path B:** push this repo to a real Git remote (GitHub/GitLab/
  Bitbucket — separate explicit action), then in Vercel: Add New Project,
  import it, set **Root Directory = `website`**, Next.js framework
  (auto-detected), default build/install commands. Add every environment
  variable per the table in that doc before first deploy — critically,
  `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`/`STRIPE_PRICE_*` must be
  test-mode in Preview, and `RATE_LIMIT_STORE_URL`/`RATE_LIMIT_STORE_TOKEN`
  are required in both Preview and Production (durable-store guard).

## 9. Unresolved owner decisions

1. **Company name resolved mid-audit: White Oak Operations.** Not yet
   applied anywhere in the codebase (still reads "Practical AI
   Operations" throughout) — this is the very next task, done as its own
   change so it doesn't get lost in this audit's diff.
2. Legal entity name, mailing address, phone, support/privacy email —
   still placeholder-free (intentionally omitted, not fabricated) on
   `/about`, `/privacy`, `/terms`.
3. Governing law/venue and counsel selection — now explicitly documented
   as *not* assumed to be New York; still needs an actual decision.
4. CRM, email, scheduling, analytics, e-signature vendor selection.
5. Favicon — deferred to the rename pass so it reflects the real brand.
6. `_source_package/` Git-tracking removal — recommended, not executed.

## 10. Remaining production blockers

- No Stripe account connected anywhere (test or live) — `npm run
  stripe:sync` has never been run.
- No Vercel project exists (permission-blocked).
- No durable rate-limit/idempotency store (Upstash or equivalent)
  provisioned yet.
- No CRM/email vendor configured — contact form currently has zero real
  destinations (correctly fails closed once deployed to a production-like
  environment without them).
- Legal drafts unreviewed by counsel.
- IONOS DNS untouched (no access; domain undecided).
