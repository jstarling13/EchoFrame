# Preview deployment attempt — status report

**Date:** 2026-08-29 | **Branch:** `website-implementation` (not merged)
No merge to `main`. No Production deploy. No IONOS DNS changes. No live
Stripe objects. Stripe test mode only, throughout.

## Bottom line

**Deployment is still blocked — same issue as before, retested and
confirmed.** No Vercel project exists, which also means no Preview
environment variables can have been configured in Vercel yet (there is
nowhere to put them without a project). Everything below explains exactly
what was verified, what's genuinely ready, and the one blocking action
needed before any of steps 1–13 in your request can actually run.

## What was completed

### 1. No-public-Checkout documentation (fully done)

Added `website/docs/NO_PUBLIC_CHECKOUT.md` stating plainly: White Oak
Operations sells scoped professional services; the approved journey is
**Fit call → Qualification → Proposal → Signed MSA/SOW → Private Stripe
deposit invoice or payment link → Kickoff.** No public purchase button
exists for O1–O5.

Also fixed copy that contradicted this — `OfferTable`/`OfferDetail`
previously said "due at checkout," implying self-serve purchase. Now
reads "initial payment ... invoiced privately after a signed SOW — not a
public checkout" everywhere pricing appears, and every offer page/`/services`
now visibly renders the six-step journey (`components/EngagementJourney.tsx`).

Added a regression test (`tests/no-public-checkout.test.ts`) that fails
the build if any page/component ever references the checkout API route,
or if the offer-detail CTA stops linking to `/contact`. Confirmed by
`grep`: zero references to `api/stripe/checkout` anywhere in `app/` or
`components/`.

### 2. Re-verified everything that's testable without a live deployment

| Check | Result |
|---|---|
| `tsc --noEmit` | Pass, 0 errors |
| `eslint .` | Pass |
| `vitest run` | **Pass, 72/72** (2 new tests added this session) |
| `next build` | Pass, 25 routes |
| `robots.txt` (local build, `VERCEL_ENV` unset) | `User-Agent: *` / `Disallow: /` — confirmed correct non-production behavior |
| `/privacy`, `/terms` | Unconditional `robots: {index:false}` + visible on-page "Draft for attorney review" callout + site-wide `DraftBanner` — confirmed in source, unchanged from the prior audit |
| Production/IONOS changes | **None** — confirmed; nothing outside this repo's local files was touched |

## What's still blocked, and why

### The Vercel project-creation permission issue is unresolved

Retested directly this session with a minimal probe deploy (not the real
site — just a throwaway 3-file Next.js app, specifically to test
permission cheaply before spending effort on the full payload):

```
Vercel API error 403: {"error":{"code":"forbidden","message":"You don't have
permission to create a project.","action":"View Documentation",
"link":"https://vercel.com/docs/accounts/team-members-and-roles"}}
```

Identical to the block found in the pre-merge audit. `list_projects` on
team `EchoFrame's projects` (`team_aRAPqQAKxNgEEADhOrrt1byO`) still
returns zero projects.

**This means steps 5, 8, and 9 from your request (configure the webhook
against a real URL, deploy, run the smoke-test matrix against a live URL)
cannot happen yet** — there's no URL to point a webhook at or smoke-test,
because there's no deployment.

### Steps 1–4, 6, 7 also can't be verified from my side right now

Not because of a missing Vercel project alone — I have **no access to
any of the actual credential values** either:

- No `.env.local` in `website/` (checked — none exists).
- No `STRIPE_SECRET_KEY`, `RATE_LIMIT_STORE_URL/TOKEN`,
  `EMAIL_PROVIDER_API_KEY`, or any other secret is set in the shell
  environment my tools run in (checked every required variable —
  all unset).
- There is no Vercel MCP tool available to me that lists or sets a
  project's environment variables (I checked the full available tool
  set) — so even once a project exists, I cannot read what's configured
  in it, only infer behavior indirectly by hitting the deployed URL.
- I will not ask you to paste `STRIPE_SECRET_KEY` or any other secret
  into this chat — that's a hard rule I follow regardless of what's
  convenient.

So "the required Preview accounts and environment variables are now
available" likely means you have the credential **values** ready (a
Stripe test key, a Resend API key, an Upstash database) — but they can't
be *in Vercel* yet, because the project itself doesn't exist. That's the
actual blocking step, ahead of everything else in your list.

## Exact unblocking action (same as documented previously, still current)

Pick one:

- **Path A:** In the Vercel dashboard, open **Team Settings → Members**
  for `EchoFrame's projects` and grant the connected integration's
  role project-creation permission
  (https://vercel.com/docs/accounts/team-members-and-roles).
- **Path B:** Push this repo to a GitHub/GitLab/Bitbucket remote
  yourself, then in the Vercel dashboard: **Add New → Project**, import
  it, set **Root Directory = `website`** (Next.js auto-detected).

## What happens next, once a project exists

I can proceed through your numbered list in this order (rewritten for
the real dependency chain — webhook config and smoke-testing need a live
URL, so deploy comes first):

1. Deploy `website-implementation` to Preview (direct-file deploy, no
   Git remote needed if you go with Path A).
2. Once deployed, verify noindex/nofollow, draft-legal-page labeling, and
   basic route health directly against the live URL.
3. For Stripe test objects: you run `STRIPE_SECRET_KEY=sk_test_xxx npm
   run stripe:sync` yourself, from `website/` — I never see the key —
   and share back only the printed `STRIPE_PRICE_*` values (not secrets)
   for me to record. Same for the Resend/Upstash values: you set them
   directly in Vercel's Preview environment variables yourself; I can't
   write them even if you gave them to me, since no such Vercel API tool
   is available to me.
4. For the Stripe webhook: once the Preview URL is known, either you
   create the webhook endpoint in the Stripe dashboard pointing at
   `<preview-url>/api/stripe/webhook` and paste the resulting
   `STRIPE_WEBHOOK_SECRET` into Vercel yourself, or tell me to attempt it
   via the Stripe API — but that still requires your test key to be
   locally accessible to me somehow, which brings us back to the same
   constraint.
5. I then run the full smoke-test matrix against the live URL myself via
   HTTP (route health, contact-form submission outcome, checkout 503 vs
   303 behavior, headers) and report back with evidence — no secrets
   ever pass through me in that flow, since the deployed app reads its
   own environment variables server-side.

## Known gaps

- Vercel project does not exist — hard blocker for steps 5, 8, 9, 10, 11
  (10 and 11 were verified locally instead, as noted above, but a live
  check is still worth doing once deployed).
- No Stripe test objects created — `npm run stripe:sync` has never been
  run (needs Action 3 above).
- No Resend/Upstash values configured anywhere — needs a project to
  configure them into.
- Screenshots of a live Preview: not possible yet, no live URL.

## Owner checklist (condensed)

- [ ] Fix Vercel project-creation permission (Path A) or push to a Git
      remote and import manually (Path B)
- [ ] Tell me once one of those is done — I'll deploy immediately after
- [ ] Run `npm run stripe:sync` with your own test key, share back the
      printed Price IDs (not the key)
- [ ] Set Preview environment variables in Vercel yourself (exact list in
      `website/docs/PREVIEW_READINESS.md` §2) — I cannot write these for
      you
- [ ] Create the Stripe Preview webhook endpoint (once the Preview URL
      exists) and set `STRIPE_WEBHOOK_SECRET` in Vercel yourself
- [ ] Confirm when ready for me to run the full smoke-test matrix against
      the live URL
