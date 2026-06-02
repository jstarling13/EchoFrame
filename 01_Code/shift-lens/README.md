# Shift Lens

> *"Some shifts are paying for themselves. Others are quietly bleeding you out.
> Now you can tell which is which."* — `echoframe-site/intelligence/strata.html`

Shift Lens is a complete backend for mapping POS revenue and employee time-punch data into 
shift-by-shift P&L analysis. It ingests raw transaction and labor data, maps them to shift blocks,
computes financial metrics, and flags underperforming shifts with recommendations.

This is the page's core promise end to end: **ingest raw data → map every shift → compute P&L →
weekly Shift Report → underperformer flags → schedule recommendations.** Pure Python, PostgreSQL.

## Features

### MVP (Core P&L Engine)
- Computes per-shift labor %, contribution (revenue − labor), and a status:
  `healthy` / `watch` / `underperforming` / `no_revenue`.
- Accepts labor as a direct `labor_cost` **or** `labor_hours × avg_wage`.
- Flags underperformers (labor far over target, or losing money) with an action for each.
- Aggregates the week: total revenue/labor, overall labor %, best & worst shift.
- Configurable target labor % (default 30%, a restaurant norm).

### Extended Backend (v0.2)
- **Raw data ingestion:** Ingest POS transactions and time-punch data from CSV/API
- **Shift mapping algorithm:** Assign transactions to nearest shift block
- **Labor allocation:** Split employee labor costs across overlapping shifts (proration)
- **Database persistence:** SQLAlchemy + PostgreSQL for transaction history
- **Historical trending:** Query shift performance over 30+ days
- **Weekly aggregation:** By-day breakdowns and performance metrics

## Run it

### Offline Demo (No Database)
```bash
cd 01_Code\shift-lens
pip install -r requirements.txt
python demo_etl.py          # Full ETL pipeline demo
python demo.py              # Original MVP demo (pre-joined shifts)
```

### Full Backend with Database
```bash
# Setup (one-time)
createdb shift_lens
cp .env.example .env        # Edit .env with DB credentials
python -c "from db import init_db; init_db()"

# Run API
uvicorn api_extended:app --reload --port 8012
```

### MVP API (Original)
```bash
uvicorn api:app --reload --port 8012
POST /api/analyze
```

### Extended API (New)
```
GET  /health
POST /api/ingest/transactions
POST /api/ingest/time-punches
POST /api/process-day                          # Full ETL pipeline
GET  /api/weekly-report/{location_id}
GET  /api/shift-history/{shift_id}
GET  /api/weekly-aggregate/{location_id}
```

## Architecture

**Three execution modes:**

1. **Offline Demo** (`demo.py`, `demo_etl.py`) — No database, sample data
2. **MVP API** (`api.py`) — Pre-joined shift rows only (original)
3. **Full Backend** (`api_extended.py`) — Raw data ingestion + database + full ETL

## Testing

```bash
python -m pytest tests/ -v              # All tests
python -m pytest tests/test_shift_mapper.py -v      # Specific module
```

Tests cover:
- Shift mapping (transaction → nearest shift)
- Labor allocation (split shifts, wage rates)
- P&L classification (healthy/watch/underperforming)

## Data Model

**Raw Inputs:**
- `POSTransaction` — timestamp, amount, order_id
- `TimePunch` — employee_id, clock_in, clock_out, wage

**Computed:**
- `ShiftMapping` — transaction/punch ↔ shift + allocation amounts
- `ShiftPLResult` — aggregated revenue, labor, status per shift per day

**Configuration:**
- `ShiftDefinition` — shift_name, day_of_week, start_time, end_time
- `Employee` — id, name, base_wage

## Key Design Decisions

- **Transaction allocation:** Assigned to **nearest shift** (not prorated)
- **Labor allocation:** **Proportionally split** across overlapping shifts
- **Persistence:** SQLAlchemy ORM with PostgreSQL
- **Timezone:** Single configured timezone (configurable in .env)
- **Target labor %:** Restaurant default 30% (configurable per request)

See [SETUP.md](SETUP.md) for detailed installation and API documentation.
