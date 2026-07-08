"""
EchoFrame — real benchmark loader
─────────────────────────────────────────────────────────────────────────────
Reads government-sourced expense ratios cached by the fetch scripts
(fetch_irs_soi.py, fetch_bls_qcew.py, fetch_census_cbp.py) and hands them to
clarity_engine in the same shape as the existing hardcoded
INDUSTRY_BENCHMARKS dict, so the swap is a one-line change with zero risk:

    from benchmarks.loader import get_benchmarks
    benchmarks = get_benchmarks(industry, fallback=INDUSTRY_BENCHMARKS.get(industry, DEFAULT_BENCHMARKS))

Design choice: this reads from small local JSON files, not a live API call
per report. Government data changes quarterly at the fastest (QCEW) and
every 1-3 years at the slowest (IRS SOI) — refetching it per customer report
would be slow, pointless, and a good way to get IP-blocked by a government
API. The fetch_*.py scripts are meant to run standalone (cron / manual),
writing into benchmarks/data/*.json; this loader only ever reads that cache.

NOTHING BREAKS IF THE CACHE IS EMPTY. Every lookup falls back to whatever
estimate clarity_engine already had, so this can be wired in before any real
data exists and shipped safely.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmarks.naics_crosswalk import get_naics

DATA_DIR = Path(__file__).resolve().parent / "data"
IRS_SOI_FILE = DATA_DIR / "irs_soi_ratios.json"
BLS_QCEW_FILE = DATA_DIR / "bls_qcew_wages.json"
CENSUS_CBP_FILE = DATA_DIR / "census_cbp.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        # A corrupt or half-written cache file should never take down a
        # customer report — treat it as "no real data yet" and fall back.
        return {}


def get_benchmarks(industry_key: str, fallback: dict) -> dict:
    """Real IRS SOI ratios for this industry's NAICS sector, if we have them
    cached; otherwise the existing hardcoded estimate (`fallback`)."""
    naics = get_naics(industry_key)
    if naics is None:
        return fallback

    soi_data = _load_json(IRS_SOI_FILE)
    sector_ratios = soi_data.get(naics["naics_sector"])
    if not sector_ratios:
        return fallback

    # Only override the line items the real data actually covers; keep the
    # hardcoded estimate for anything IRS SOI doesn't break out (Software,
    # Insurance, etc. often aren't separate lines in the public tables).
    merged = dict(fallback)
    merged.update(sector_ratios)
    return merged


def get_regional_wage_context(industry_key: str, area_fips: str | None = None) -> dict | None:
    """Real BLS QCEW average weekly wage for this industry (and area, if
    given), if cached. Returns None if we don't have it yet — callers should
    treat this as optional color, not something to build a hard dependency
    on (regional cuts will be sparse until fetch_bls_qcew.py has run for the
    specific counties EchoFrame customers are actually in)."""
    naics = get_naics(industry_key)
    if naics is None:
        return None
    wages = _load_json(BLS_QCEW_FILE)
    key = f"{naics['naics_6']}:{area_fips}" if area_fips else naics["naics_6"]
    return wages.get(key)


def get_regional_density(industry_key: str, state_fips: str) -> dict | None:
    """Real Census CBP establishment count / employment / avg payroll per
    employee for this industry in a given state, if cached. Returns None if
    we don't have it yet (either not fetched, or Census itself has no data
    at this NAICS+state combination — some detailed codes are suppressed)."""
    naics = get_naics(industry_key)
    if naics is None:
        return None
    cbp = _load_json(CENSUS_CBP_FILE)
    return cbp.get(f"{naics['naics_6']}:{state_fips}")


def coverage_report(industry_keys: list[str]) -> dict:
    """How many of our industries currently have REAL data behind them vs
    still falling back to the hardcoded estimate. Useful for a one-line
    startup log or an admin page once fetch scripts have run a few times."""
    soi_data = _load_json(IRS_SOI_FILE)
    real, estimated = [], []
    for key in industry_keys:
        naics = get_naics(key)
        if naics and soi_data.get(naics["naics_sector"]):
            real.append(key)
        else:
            estimated.append(key)
    return {"real": real, "estimated": estimated, "real_count": len(real), "estimated_count": len(estimated)}
