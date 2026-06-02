# Shift Lens Backend Setup Guide

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip

## Installation

1. **Create virtual environment:**
   ```bash
   cd shift-lens
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create PostgreSQL database:**
   ```bash
   createdb shift_lens
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your database credentials:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/shift_lens
   TIMEZONE=US/Eastern
   DEFAULT_TARGET_LABOR_PCT=30.0
   ```

5. **Initialize database tables:**
   ```bash
   python -c "from db import init_db; init_db()"
   ```

## Running the Application

### Full API with Database
```bash
uvicorn api_extended:app --reload --port 8012
```

Then test with:
```bash
curl http://localhost:8012/health
```

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

### Health Check
```
GET /health
```

### Data Ingestion
```
POST /api/ingest/transactions
POST /api/ingest/time-punches
```

### Process Day
```
POST /api/process-day
```

Trigger full ETL pipeline for a day (ingest → map → allocate → persist → compute P&L).

### Reports
```
GET /api/weekly-report/{location_id}?week_start=2024-01-15
GET /api/shift-history/{shift_id}?location_id=columbus-main&days=30
GET /api/weekly-aggregate/{location_id}?week_start=2024-01-15
```

### Database Management
```
POST /api/initialize-db
```

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
