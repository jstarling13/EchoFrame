# Shift Lens (MVP)

> *"Some shifts are paying for themselves. Others are quietly bleeding you out.
> Now you can tell which is which."* — `echoframe-site/intelligence/strata.html`

Shift Lens maps each shift's labor cost against its revenue, computes a shift-by-shift P&L,
flags the shifts that are underperforming, and gives a concrete recommendation for each.

This is the page's core promise end to end: **map every shift → weekly Shift Report →
underperformer flags → schedule recommendations.** Pure Python, no external calls.

## What it does
- Computes per-shift labor %, contribution (revenue − labor), and a status:
  `healthy` / `watch` / `underperforming` / `no_revenue`.
- Accepts labor as a direct `labor_cost` **or** `labor_hours × avg_wage`.
- Flags underperformers (labor far over target, or losing money) with an action for each.
- Aggregates the week: total revenue/labor, overall labor %, best & worst shift.
- Configurable target labor % (default 30%, a restaurant norm).

## Run it

```powershell
cd 01_Code\shift-lens
pip install -r requirements.txt

python demo.py                         # offline sample weekly report
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8012   # HTTP API
```

### API
- `GET  /health`
- `POST /api/analyze`:

```json
{
  "shifts": [
    {"label": "Sat Dinner", "revenue": 5200, "labor_cost": 1300},
    {"label": "Tue Lunch", "revenue": 600, "labor_hours": 26, "avg_wage": 15}
  ],
  "target_labor_pct": 30
}
```

Returns per-shift results, ranked underperformers, best/worst shift, totals, and `report_text`.

## Assumptions / scope
- **Input is already-joined shift rows** (revenue + labor per shift). The page promises a POS +
  scheduling integration; that join is the documented seam and happens upstream in production —
  the P&L math here is what it feeds. Sample/CSV input stands in for the live POS feed.
- "Contribution" is revenue − labor only (the shift-level lever the product is about); it is not
  full shift profit (no allocated rent/COGS). This matches the page's labor-vs-revenue framing.
- Default target labor % is a restaurant norm; pass `target_labor_pct` for other models.
- No auth/billing/persistence (flagship Stripe surface fronts it). Informational only.
