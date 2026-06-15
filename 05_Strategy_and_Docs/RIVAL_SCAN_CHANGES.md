# Rival Scan — audit + finish (changes log)

You asked for a from-scratch Rival Scan build. It turned out **Rival Scan was already
~90% implemented in the EchoFrame root** (the `echoframe-rate-watch` Next.js app:
NextAuth v5 + Prisma + Resend + Firecrawl + Vercel Cron, with the `Competitor` /
`CompetitorSnapshot` / `Alert` schema, rivals API, dashboard, differ, emailer, and three
cron routes). So rather than rebuild and duplicate it (you also have a second Rival Scan
in the standalone `Veris` repo), I audited it and fixed the real gaps. No rebuild.

> Architecture note: this EchoFrame-root app uses **NextAuth**, while your sibling
> product apps (Oryn, Veris) use **Clerk**. Worth standardizing portfolio-wide at some
> point — flagged, not changed here.

---

## What was already correct (left as-is)
- `prisma/schema.prisma` — `User/Account/Session/VerificationToken` + `Competitor`,
  `CompetitorSnapshot`, `Alert`. Matches your Section A exactly.
- `lib/auth.ts`, `middleware.ts` — NextAuth v5, route protection for `/dashboard`,
  `/rivals`, `/api/rivals`.
- `app/api/rivals/*` — CRUD for competitors (auth-scoped to the tenant).
- `app/dashboard/*` — competitor list, add-competitor form (`dashboard/rivals/new`),
  detail view (`dashboard/rivals/[id]`). Matches Section D.
- `lib/alerts/emailer.ts` daily + weekly HTML emails; daily marks alerts `sentAt`.
- `vercel.json` — crons at 06:00 (scrape), 08:00 (alerts), 09:00 Fri (digest) UTC.

## What I fixed (the gaps)

| File | Problem | Fix |
|---|---|---|
| `lib/scraping/firecrawl.ts` | `scrapeGoogleBusiness` returned **`Math.random()`** → fake review/rating data, false alerts | Real `fetchGooglePlacesData` (Place Details by `place_id`, else Text Search by name+location) + `fetchYelpData` (Fusion) + `fetchReviewMetrics` wrapper. **Returns `null` when no key/match — never fabricated.** |
| `lib/scraping/firecrawl.ts` | Firecrawl request used **v0** `pageOptions` against the **v1** endpoint | v1 payload: `formats: ["markdown"], onlyMainContent: true` + 60s timeout |
| `app/api/cron/*` (all 3) | Routes exported **only `POST`**, but **Vercel Cron calls `GET`** → 405, crons never ran | Added `GET` handlers that delegate to `POST` (CRON_SECRET check preserved) |
| `app/api/cron/scrape-competitors` | Used the mock google call | Uses `fetchReviewMetrics({ name, location, googleBusinessUrl, yelpUrl })` |
| `lib/alerts/differ.ts` | Section C correlation ("more reviews → did rating drop?") was missing | New null-safe block: reviews ↑ **and** rating ↓ ⇒ one HIGH `REVIEW_RATING_DROP` alert; otherwise independent `REVIEW_UPDATE` / `RATING_CHANGE` |
| `lib/alerts/emailer.ts` | `from: alerts@rivalsan.com` (unverified/typo domain) → Resend won't send; hardcoded dashboard links | Env-driven `RESEND_FROM_EMAIL` (defaults to `onboarding@resend.dev`) + `NEXT_PUBLIC_APP_URL` |
| `.env.example` | Missing keys | Added `GOOGLE_PLACES_API_KEY`, `YELP_API_KEY`, `RESEND_FROM_EMAIL`, `NEXT_PUBLIC_APP_URL` |

---

## Run + verify on your machine

> I couldn't run the build in this environment (network/disk/process limits in the
> sandbox — same as on the Oryn task). These are the exact steps for your machine.

```powershell
cd C:\Users\jacob\OneDrive\Businesses\EchoFrame
npm install
copy .env.example .env        # then fill in real values (see below)
npm run prisma:generate
npm run prisma:migrate         # creates/updates tables (dev). Review before running on a shared DB.
npm run build                  # must be green
npm run dev                    # http://localhost:3000
```

**Keys to fill for live data:**
- `DATABASE_URL` — your Postgres/Supabase.
- `GOOGLE_PLACES_API_KEY` — enable **Places API** in Google Cloud. Without it, review
  count/rating are skipped (null), not faked.
- `RESEND_API_KEY` + `RESEND_FROM_EMAIL` — use `onboarding@resend.dev` until your domain
  is verified in Resend.
- `FIRECRAWL_API_KEY`, `CRON_SECRET`, `NEXTAUTH_SECRET`, an OAuth provider (Google/GitHub).
- `YELP_API_KEY` — optional fallback; leave blank to skip.

**Test the cron jobs locally** (they now accept GET, like Vercel Cron):
```powershell
# scrape -> snapshot -> diff -> alerts
curl -H "Authorization: Bearer %CRON_SECRET%" http://localhost:3000/api/cron/scrape-competitors
# send queued alerts (run scrape twice with a change in between to generate a diff)
curl -H "Authorization: Bearer %CRON_SECRET%" http://localhost:3000/api/cron/send-alerts
# weekly digest
curl -H "Authorization: Bearer %CRON_SECRET%" http://localhost:3000/api/cron/send-weekly-digest
```
(In dev, `NODE_ENV !== "production"` so the auth header is optional, but it mirrors prod.)

**End-to-end smoke test:** sign in → `/dashboard` → add a competitor (name + website +
Google Business URL) → hit the scrape cron → hit it again after the competitor changes a
price/promo (or just confirm the first snapshot lands) → hit send-alerts → check the email.

---

## Suggested follow-ups (not done)
- Decide the canonical Rival Scan home (this EchoFrame-root app vs the `Veris` repo) and
  retire the other to avoid drift.
- Standardize auth across the portfolio (NextAuth here vs Clerk in Oryn/Veris).
- Add a per-user toggle for alert/digest opt-in if you want users to control cadence.
