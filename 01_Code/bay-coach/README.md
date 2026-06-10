# Bay Coach (MVP)

> *"The right service recommendation at every write-up — based on what the vehicle actually
> needs, not what the advisor happened to remember."* — `echoframe-site/ops/baysignal.html`

Bay Coach takes a vehicle's current mileage and service history and tells the advisor which
services are **overdue / due / coming up** at write-up, ranked by urgency, each with a reason.

Pure Python, no external calls.

## What it does
- Compares mileage-since-last against a maintenance-interval rules table (oil, tires, brakes,
  fluids, plugs, belts, …).
- Per service: status (`overdue` / `due` / `upcoming` / `ok`), miles since last, miles until due,
  and a plain reason the advisor can read to the customer.
- Treats a never-recorded service as due (and says so, so the advisor confirms).
- Ranks recommendations most-urgent-first; counts overdue/due.

## Run it

```powershell
cd 01_Code\bay-coach
pip install -r requirements.txt

python demo.py                         # offline sample write-up
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8014   # HTTP API
```

### API
- `GET  /health`
- `POST /api/recommend`:

```json
{
  "current_mileage": 68400, "year": 2019, "make": "Toyota", "model": "Camry",
  "history": [
    {"service": "Oil & filter change", "mileage": 62000},
    {"service": "Brake inspection", "mileage": 55000}
  ]
}
```

Returns ranked `recommendations`, the `actionable` subset, overdue/due counts, and a
`writeup_text` the advisor can read.

## Assumptions / scope
- **Input is the vehicle + history the shop management system holds.** That integration is the
  documented seam (the page's "connect your shop management system" step); the recommendation
  logic here is what it feeds. Sample/JSON input stands in for the live SMS feed.
- Uses a **standard passenger-vehicle interval table** (`DEFAULT_RULES`); per-make/model tables
  drop in without changing the engine.
- Recommendations are mileage/history-based, **not** a physical inspection — the write-up text
  says so. Advisor presents, customer decides (matches the page).
- Month-based-only intervals are surfaced for manual review in the MVP (mileage is the primary
  signal); full time-based logic is a later iteration.
- No auth/billing/persistence. Informational only.
