# Permit Watch (MVP)

> *"Every license, registration, and permit on one dashboard — with a heads-up 30 days
> before anything expires."* — `echoframe-site/ops/permitwatch.html`

Permit Watch puts every compliance item (registrations, licenses, permits, insurance,
inspections) on one dashboard, computes days-to-expiry and a status, groups items by
vehicle/entity, and produces the **30-day alert digest** the page promises.

Pure Python, no external calls.

## What it does
- Per item: days-to-expiry + status — `expired` / `critical` (≤7d) / `due_soon` (≤window) /
  `upcoming` / `ok`.
- Dashboard: all items sorted most-urgent-first, status counts, alerts list, expired list.
- **Per-entity grouping** (per-vehicle tracking) — the page's "per-vehicle" feature.
- `render_alert_digest`: the inbox-ready 30-day heads-up (only items needing attention).
- Configurable alert window (default 30 days); critical threshold fixed at 7 days.

## Run it

```powershell
cd 01_Code\permit-watch
pip install -r requirements.txt

python demo.py                         # offline sample dashboard + digest
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8013   # HTTP API
```

### API
- `GET  /health`
- `POST /api/dashboard`:

```json
{
  "items": [
    {"name": "Vehicle registration", "category": "registration", "expiry_date": "2026-06-20", "entity": "Van 12", "identifier": "GA ABC123"},
    {"name": "Business license", "category": "license", "expiry_date": "2026-09-01"}
  ],
  "alert_window_days": 30
}
```

Returns the full dashboard (items, counts, alerts, expired, grouped by entity) and an
inbox-ready `alert_digest`.

## Assumptions / scope
- Input is the list of items the owner enters (the page's "enter your fleet and licenses" step).
  No external DMV/licensing integration — items are user-maintained, which is exactly what the
  page describes for the MVP.
- The "alerts hit your inbox 30 days out" delivery is a thin scheduled wrapper (daily cron →
  `render_alert_digest` → email) over this engine; the digest text is built here, sending is not
  (and would reuse the flagship's Resend integration). Documented seam.
- Document storage/history (a page feature) is out of MVP scope — noted for a later iteration.
- No auth/billing/persistence. Informational only.
