# Rate Watch (MVP)

> *"Every vendor you pay has a market rate. Find out how many of yours are above it."*
> — `echoframe-site/intelligence/oryn.html`

Rate Watch benchmarks each vendor you pay against a market-rate band for its category,
ranks where you're overpaying (in real dollars), and flags contracts that renew soon so
you renegotiate before you auto-renew at the old rate.

This is the page's core promise, end to end: **enter vendors → benchmark → report with the
gaps + renewal alerts.** Pure Python, no external calls.

## What it does
- Compares each vendor's monthly spend to a `(low, typical, high)` market band for its category.
- Classifies each as `over` / `within` / `under` / `no_benchmark`.
- Computes overpayment ($/mo and %), ranks largest gaps first, totals monthly & annual savings.
- Flags renewals due within a window (default 30 days) — the page's "30 days before renewal" promise.
- Emits a plain-English report (`render_report_text`) and a JSON API response.

## Run it

```powershell
cd 01_Code\rate-watch
pip install -r requirements.txt

python demo.py                         # offline sample report
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8011   # HTTP API
```

### API
- `GET  /health` — liveness + benchmark category count
- `GET  /api/categories` — the market-rate bands in use
- `POST /api/analyze` — analyze a list of vendors:

```json
{
  "vendors": [
    {"name": "FirstData", "category": "merchant processing", "monthly_cost": 980, "renewal_date": "2026-06-15"},
    {"name": "Gusto", "category": "payroll software", "monthly_cost": 75}
  ],
  "renewal_window_days": 30
}
```

Returns per-vendor findings, ranked overpayers, renewals due, totals, and a `report_text`.

## Assumptions / scope
- **Market-rate bands are a curated sample table** (`engine.MARKET_RATES`), mirroring how the
  flagship Clarity Report ships curated industry benchmarks. In production this is replaced by a
  real local-market data feed; the comparison logic is unchanged. This is the documented seam.
- "Local market" is approximated by national small-business bands in the MVP (no geo input yet).
- No persistence/auth/billing — those live in the flagship's Stripe surface, which can front this.
- Renewal alerts are computed on demand; scheduling the 30-day email is a thin cron wrapper (not
  built here) over `analyze_vendors(...)["renewals_due"]`.
- Informational only — not a quote or financial advice (matches EchoFrame's site disclaimer).
