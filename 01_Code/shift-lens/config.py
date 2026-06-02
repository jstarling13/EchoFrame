import os
from pathlib import Path
from dotenv import load_dotenv

# Load ONLY this project's .env (next to this file). We deliberately do not let
# python-dotenv walk up the directory tree, so an unrelated ancestor .env (e.g. in
# the user's home folder) can never leak credentials/config into this service.
_PROJECT_ENV = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_PROJECT_ENV, override=False)

# Database
# --------
# Defaults to a local SQLite file so the engine runs zero-config out of the box.
# For production, set DATABASE_URL to your PostgreSQL DSN, e.g.
#   postgresql://user:password@localhost:5432/shift_lens
# (see .env.example). The ORM, ETL, and service layers are DB-agnostic.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///shift_lens.db")

# Timezone used to interpret incoming POS / punch timestamps.
TIMEZONE = os.getenv("TIMEZONE", "US/Eastern")

# Default target labor cost as a percentage of revenue (restaurant norm).
DEFAULT_TARGET_LABOR_PCT = float(os.getenv("DEFAULT_TARGET_LABOR_PCT", 30.0))

# API key required by ingest/process endpoints. If unset, auth is disabled
# (convenient for local dev; set this in any shared/production deployment).
API_KEY = os.getenv("SHIFT_LENS_API_KEY", "")


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")
