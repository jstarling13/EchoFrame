# Shift Lens Backend Setup Guide

## Prerequisites

- Python 3.10+
- pip
- PostgreSQL 12+ *(optional — the engine defaults to SQLite for zero-config local runs)*

## Quick Start (zero-config, SQLite)

```bash
cd shift-lens
pip install -r requirements.txt

python seed_data.py --reset            # create tables + seed a week of demo data
uvicorn api_extended:app --port 8012   # start the API + dashboard
```

Then open **http://localhost:8012/** — the live dashboard. Click
“Sync & Analyze Day” to pull mock POS + timesheet data and render a shift P&L.

With no `DATABASE_URL` set, the app writes to a local `shift_lens.db` SQLite file.

## Production (PostgreSQL)

1. **Create the database:**
   ```bash
   createdb shift_lens
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/shift_lens
   TIMEZONE=US/Eastern
   DEFAULT_TARGET_LABOR_PCT=30.0
   SHIFT_LENS_API_KEY=choose-a-strong-key     # enables auth on mutating endpoints
   ```

3. **Run migrations (Alembic):**
   ```bash
   alembic upgrade head
   ```

4. **Run the API:**
   ```bash
   uvicorn api_extended:app --port 8012
   ```

> The ORM, ETL, connectors, and service layers are database-agnostic — the only
> difference between local and production is the `DATABASE_URL`.

## Database Migrations (Alembic)

```bash
alembic upgrade head                          # apply all migrations
alembic revision --autogenerate -m "message"  # generate a new migration after model changes
alembic current                               # show current revision
alembic downgrade -1                          # roll back one revision
```

The initial migration under `migrations/versions/` mirrors all six models.
`migrations/env.py` reads `DATABASE_URL` from `config.py`, so migrations always
target the same database as the app.

## Authentication

Mutating endpoints (`/api/ingest/*`, `/api/process-day`, `/api/sync-day`,
`/api/initialize-db`) require the header `X-API-Key` to match `SHIFT_LENS_API_KEY`
when that env var is set. If it is unset (local dev), auth is disabled. Read-only
report endpoints are always open.

### Offline Demo (No Database Required)
```bash
python demo_etl.py
```

This runs the full ETL pipeline with sample data, demonstrating:
- Raw data ingestion
- Transaction → shift mapping
- Labor → shift allocation (with split shifts)
- P&L computation
- Weekly report generation

### MVP Demo (Original)
```bash
python demo.py
```

## Database Schema

The following tables are created automatically:

- **pos_transactions** — Raw POS data (timestamp, amount, order_id)
- **employees** — Employee master data (id, name, base_wage)
- **time_punches** — Clock-in/out records (employee_id, clock_in, clock_out)
- **shift_definitions** — Business shift blocks (shift_name, day_of_week, start_time, end_time)
- **shift_mappings** — Transaction ↔ Shift ↔ Labor allocation (revenue_allocation, labor_allocation)
- **shift_pl_results** — Computed P&L per shift per day (total_revenue, total_labor_cost, status)

## API Endpoints

### Dashboard
```
GET /                          # redirects to the live dashboard
GET /app/dashboard.html        # standalone branded UI (calls the API)
```

### Health & Config
```
GET /health
GET /api/shifts/{location_id}  # list configured shift blocks
```

### Connector Sync (production integration seam)
```
GET  /api/sources              # which sources are usable now (square needs a token)
POST /api/sync-day             # pull a day from POS + timesheet connectors, then run the pipeline
POST /api/sync-now 🔒          # trigger one auto-sync pass for today across configured locations
GET  /api/scheduler            # auto-sync scheduler config/state
```
Body for sync-day: `{date, location_id, pos_source, timesheet_source, target_labor_pct}`.
`pos_source`/`timesheet_source` are `"mock"` or `"square"` (Square needs
`SQUARE_ACCESS_TOKEN`). Add more by implementing the `POSConnector` /
`TimesheetConnector` interface in `connectors/`.

### Real-time (live) ingestion
```
POST /api/webhooks/pos 🔒        # push one sale; the day is recomputed live
POST /api/webhooks/timesheet 🔒  # push one completed punch; recomputed live
GET  /api/day/{location_id}?date=YYYY-MM-DD   # read one day's live P&L (dashboard polls this)
```

The live dashboard (`/app/dashboard.html`) has a **Go Live** toggle (polls
`/api/day` every 3s) and a **Send Test Sale** button that posts a POS webhook so
you can watch the P&L update in real time — no external accounts required.

#### Square (real live data)
1. Set `SQUARE_ACCESS_TOKEN` (and `SQUARE_API_BASE=https://connect.squareupsandbox.com` for sandbox).
2. `GET /api/sources` should now list `square`.
3. `POST /api/sync-day` with `"pos_source":"square","timesheet_source":"square"`,
   or set `AUTO_SYNC_POS_SOURCE=square` + `AUTO_SYNC_ENABLED=true` for hands-off sync.

#### Auto-sync scheduler
Set `AUTO_SYNC_ENABLED=true` to run a background loop that re-syncs today every
`AUTO_SYNC_INTERVAL_SECONDS` for `AUTO_SYNC_LOCATIONS`. Idempotent — never double-counts.

### Data Ingestion (explicit payloads) 🔒
```
POST /api/ingest/transactions
POST /api/ingest/time-punches
POST /api/process-day          # full ETL from an explicit payload
```

### Reports
```
GET /api/weekly-report/{location_id}?week_start=2024-01-15
GET /api/shift-history/{shift_id}?location_id=columbus-main&days=30
GET /api/weekly-aggregate/{location_id}?week_start=2024-01-15
```

### Admin 🔒
```
POST /api/initialize-db
```

🔒 = requires `X-API-Key` when `SHIFT_LENS_API_KEY` is set.

### Idempotency

`/api/process-day` and `/api/sync-day` clear any existing data for the
`(date, location)` before reprocessing, so re-running a day never double-counts.

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_shift_mapper.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Troubleshooting

### PostgreSQL Connection Error
- Ensure PostgreSQL is running
- Verify DATABASE_URL in .env
- Check credentials and database name

### Import Errors
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Timezone Issues
- Adjust TIMEZONE in .env to match your location
- All timestamps are assumed to be in the configured timezone

## Architecture Notes

**Three Layers:**

1. **ETL Layer** (`etl/`) — Raw data ingestion, shift mapping, labor allocation
2. **Persistence Layer** (`models/`, database) — SQLAlchemy ORM models
3. **Service Layer** (`service/`) — Business logic orchestration
4. **API Layer** (`api_extended.py`) — FastAPI endpoints

**Key Design:**
- Transactions are assigned to **nearest shift** (not prorated)
- Labor costs are **proportionally split** across overlapping shifts
- All tables are indexed by `location_id` for multi-location queries
- Results are persisted for historical analysis and trend detection

## Production Considerations

- Add authentication layer (API keys, JWT)
- Add rate limiting for API endpoints
- Add logging & monitoring
- Use connection pooling for high volume
- Consider async workers for bulk processing
- Add data validation & error recovery
- Implement audit logging for P&L changes
