# Rate Watch — 3 Client Samples (Ready to Demo)

The dev server is running. Open these URLs to show prospects a personalized
Rate Watch dashboard. Each has its own vendor portfolio, benchmarked against
**Columbus, GA** market rates, with a printable report and an email preview.

## Start / open

- **Selector (all clients):** http://localhost:3000/rate-watch
- Or double-click **`run-rate-watch.bat`** to (re)start the server.

## The three samples

| Client | Industry | Size | Annual Spend | Savings Found | Overpaying | Renewals (30d) |
|--------|----------|------|--------------|---------------|------------|----------------|
| **Riverside Family Dental** | Dental Practice | 1–10 | $32,460 | **$5,460** | 3 | 2 |
| **Chattahoochee Coffee Roasters** | Cafe & Roastery | 1–10 | $19,920 | **$1,860** | 4 | 2 |
| **Fountain City Auto Repair** | Auto Repair | 11–50 | $43,080 | **$3,120** | 4 | 3 |

Direct links:
- http://localhost:3000/rate-watch/riverside-family-dental
- http://localhost:3000/rate-watch/chattahoochee-coffee-roasters
- http://localhost:3000/rate-watch/fountain-city-auto-repair

## What to show in a demo

1. **Dashboard** — metric cards (spend / savings / renewals), red alert banner for
   overpaying vendors, sortable vendor table with status badges + renewal dates.
2. **Vendor detail** — click "View Details" on a red (Overpaying) row to show the
   rate gap and the auto-generated **renegotiation talking points** (copy button).
3. **Printable Report** — top-right "Printable Report" button → clean, branded
   one-pager. Use the browser's **Print → Save as PDF** to send to a prospect.
   (Direct: `/rate-watch/<slug>/report`)
4. **Email preview** — "Preview Email" button shows the branded renewal-alert email
   a client would receive. (Direct: `/api/rate-watch/<slug>/send-alerts`)

## Sending real emails (optional)

Email sending is wired to Resend via the REST API. Without a key it's a safe
dry-run. To actually send, set in `.env.local`:

```
RESEND_API_KEY=re_xxxxxxxx
RATE_WATCH_FROM_EMAIL="Rate Watch <you@yourdomain.com>"
```

Then POST to `/api/rate-watch/<slug>/send-alerts` with `{ "to": "client@email.com" }`.

## Operational notes (important)

This folder is shared with other tooling that keeps `prisma/schema.prisma` on
**PostgreSQL** (for a separate auth/competitive-intel app). Rate Watch runs
locally on **SQLite** using a dedicated schema: `prisma/rate-watch.prisma`.

- ✅ **To run:** use `run-rate-watch.bat` (or `npm run dev`). It uses SQLite `dev.db`.
- ✅ **To reseed:** run `reseed-rate-watch.bat`.
- ⚠️ **Do NOT run `npm run build` locally.** Its `prisma generate` step targets the
  Postgres `schema.prisma` (which lacks the SQLite client) and an injected
  `/api/cron/send-alerts` route crashes the build. Use the dev server for demos.
- If the dashboard ever 500s with "Cannot find module '@prisma/client'" or a
  missing `slug`, just run `run-rate-watch.bat` again — it regenerates the
  correct SQLite client before starting.

## Customizing the samples

Edit the `COMPANIES` and `BENCHMARKS` arrays in `prisma/seed.ts`, then run
`reseed-rate-watch.bat`. Add a new sample by appending a company object (set a
unique `slug`); it appears automatically on the selector page.
