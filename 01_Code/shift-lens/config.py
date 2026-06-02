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

# --- Square integration (real live POS + labor) ---
# Leave the token empty to keep the Square connector unavailable. Set
# SQUARE_API_BASE to https://connect.squareupsandbox.com for the sandbox.
SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN", "")
SQUARE_API_BASE = os.getenv("SQUARE_API_BASE", "https://connect.squareup.com")
SQUARE_API_VERSION = os.getenv("SQUARE_API_VERSION", "2024-10-17")
SQUARE_DEFAULT_WAGE = float(os.getenv("SQUARE_DEFAULT_WAGE", 15.0))  # fallback if a shift has no wage

# --- Auto-sync scheduler ---
# When enabled, a background loop re-syncs "today" for each location on an interval.
AUTO_SYNC_ENABLED = os.getenv("AUTO_SYNC_ENABLED", "false").lower() in ("1", "true", "yes")
AUTO_SYNC_INTERVAL_SECONDS = int(os.getenv("AUTO_SYNC_INTERVAL_SECONDS", "300"))
AUTO_SYNC_LOCATIONS = [
    s.strip() for s in os.getenv("AUTO_SYNC_LOCATIONS", "columbus-main").split(",") if s.strip()
]
AUTO_SYNC_POS_SOURCE = os.getenv("AUTO_SYNC_POS_SOURCE", "mock")
AUTO_SYNC_TIMESHEET_SOURCE = os.getenv("AUTO_SYNC_TIMESHEET_SOURCE", "mock")
AUTO_SYNC_TARGET_LABOR_PCT = float(os.getenv("AUTO_SYNC_TARGET_LABOR_PCT", DEFAULT_TARGET_LABOR_PCT))


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")
