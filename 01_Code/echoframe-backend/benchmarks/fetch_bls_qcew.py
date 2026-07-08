"""
EchoFrame — pull BLS QCEW wage data by industry (and optionally by county)
─────────────────────────────────────────────────────────────────────────────
Source: BLS Quarterly Census of Employment and Wages, Open Data CSV slices.
No API key required. Docs: https://www.bls.gov/cew/additional-resources/open-data/

URL pattern (verified against BLS docs):
    https://data.bls.gov/cew/data/api/{year}/{quarter}/industry/{naics}.csv
    https://data.bls.gov/cew/data/api/{year}/{quarter}/area/{area_fips}.csv

`quarter` is 1-4, or "a" for the annual-average slice (what we want here —
one stable number per year, not four quarterly ones).

Each industry slice returns one row per area (national + every state/county
that publishes at that NAICS depth) with, among other columns (verified live
against the 2024 restaurant NAICS 722511 slice):
    own_code, industry_code, agglvl_code, area_fips, year, qtr,
    disclosure_code, annual_avg_estabs, annual_avg_emplvl,
    total_annual_wages, avg_annual_pay, annual_avg_wkly_wage

`annual_avg_wkly_wage` is real, current, regionally specific — the number
that powers Rate Watch's "your region" claim and gives Clarity a sanity
check on the Labor Cost ratio IRS SOI provides nationally.

Writes benchmarks/data/bls_qcew_wages.json, keyed "{naics_6}" (national) and
"{naics_6}:{area_fips}" (per county/state), each -> {"avg_weekly_wage": ...,
"avg_annual_pay": ..., "employment": ..., "establishments": ..., "year": ...}.

Run standalone, not per-report:
    python -m benchmarks.fetch_bls_qcew --year 2025

Only pulls national + state totals by default (area_fips="US000" and the 50
state codes) — that's enough for the current "your region" copy without
pulling all ~3,000 counties. Pass --counties FIPS,FIPS,... to add specific
counties once we know which ones EchoFrame customers are actually in.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

from benchmarks.naics_crosswalk import CROSSWALK

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "bls_qcew_wages.json"
BASE_URL = "https://data.bls.gov/cew/data/api/{year}/a/industry/{naics}.csv"

# QCEW area_fips: "US000" = national, "{2-digit state FIPS}000" = state total,
# 5-digit = county. Default area set below = national + every state (51 incl.
# DC) — real per-state wage levels without pulling all ~3,000 counties. Pass
# --counties to add specific counties once we know which ones matter.
_STATE_FIPS = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
]
_DEFAULT_AREAS = {"US000"} | {f"{fips}000" for fips in _STATE_FIPS}


def _fetch_industry_csv(year: int, naics_6: str) -> list[dict]:
    url = BASE_URL.format(year=year, naics=naics_6)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [skip] {naics_6}: {type(e).__name__}: {e}")
        return []
    return list(csv.DictReader(io.StringIO(text)))


def _is_usable_row(row: dict) -> bool:
    # disclosure_code non-empty means BLS suppressed the value for that
    # area/industry (too few establishments to protect confidentiality).
    if row.get("disclosure_code"):
        return False
    # own_code 5 = "Private", the ownership slice we actually want (not
    # federal/state/local government establishments in the same NAICS).
    return row.get("own_code") == "5"


def fetch(year: int, area_filter: set[str] | None = None) -> dict:
    naics_codes = sorted({v["naics_6"] for v in CROSSWALK.values()})
    out: dict[str, dict] = {}

    for naics in naics_codes:
        print(f"Fetching QCEW {year} annual, NAICS {naics} ...")
        rows = _fetch_industry_csv(year, naics)
        for row in rows:
            if not _is_usable_row(row):
                continue
            area_fips = row.get("area_fips", "")
            if area_filter and area_fips not in area_filter:
                continue
            try:
                entry = {
                    "avg_weekly_wage": float(row["annual_avg_wkly_wage"]),
                    "avg_annual_pay": float(row["avg_annual_pay"]),
                    "employment": int(float(row["annual_avg_emplvl"])),
                    "establishments": int(float(row["annual_avg_estabs"])),
                    "year": year,
                }
            except (KeyError, ValueError):
                continue
            key = naics if area_fips in ("US000", "") else f"{naics}:{area_fips}"
            out[key] = entry

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, required=True, help="e.g. 2025 (most recent complete year)")
    ap.add_argument("--counties", type=str, default="", help="comma-separated 5-digit county FIPS to include (national + state totals always included)")
    args = ap.parse_args()

    area_filter = set(_DEFAULT_AREAS)
    if args.counties:
        area_filter |= {c.strip() for c in args.counties.split(",") if c.strip()}

    result = fetch(args.year, area_filter)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {len(result)} entries to {OUTPUT_FILE}")
    if not result:
        print("WARNING: nothing written — check network access and that the year has published annual data yet.")
        sys.exit(1)


if __name__ == "__main__":
    main()
