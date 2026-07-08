"""
EchoFrame — pull Census County Business Patterns (CBP) by industry + state
─────────────────────────────────────────────────────────────────────────────
Source: U.S. Census Bureau County Business Patterns API.
Requires a free API key (CENSUS_API_KEY in .env). Docs:
https://www.census.gov/data/developers/data-sets/cbp-zbp/cbp-api.html

Verified live query shape (2022 vintage, the latest CBP year at time of
writing):
    https://api.census.gov/data/2022/cbp
      ?get=ESTAB,EMP,PAYANN,NAICS2017_LABEL,NAME
      &for=state:*
      &NAICS2017={naics_6}
      &key={CENSUS_API_KEY}

Returns one row per state: establishment count, mid-March employment, and
annual payroll ($1,000s) for that NAICS code. This is regional density and
scale context (how many comparable businesses exist in a state, how many
people they employ) — NOT an expense-ratio benchmark by itself. It's the
data Rate Watch's "how many comparable businesses is this benchmark drawn
from" and "typical business size in your area" context should use; the
actual Food Cost / Labor Cost / Rent % ratios still come from IRS SOI.

Writes benchmarks/data/census_cbp.json, keyed "{naics_6}:{state_fips}" ->
{"establishments": ..., "employment": ..., "annual_payroll_thousands": ...,
"avg_payroll_per_employee": ..., "year": ...}.

Run standalone, not per-report:
    python -m benchmarks.fetch_census_cbp --year 2022
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from benchmarks.naics_crosswalk import CROSSWALK

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "census_cbp.json"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _read_census_key() -> str:
    key = os.environ.get("CENSUS_API_KEY", "").strip()
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("CENSUS_API_KEY="):
                return line.split("=", 1)[1].strip()
    print("ERROR: CENSUS_API_KEY not set (env var or .env).", file=sys.stderr)
    sys.exit(1)


def _fetch_industry(year: int, naics_6: str, key: str) -> list[dict]:
    fields = "ESTAB,EMP,PAYANN,NAICS2017_LABEL,NAME"
    url = (
        f"https://api.census.gov/data/{year}/cbp"
        f"?get={fields}&for=state:*&NAICS2017={naics_6}&key={key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"  [skip] {naics_6}: HTTP {e.code}")
        return []

    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        # Census returns an HTML error page (still HTTP 200) for a bad key,
        # a bad NAICS code, or an unsupported field combination.
        print(f"  [skip] {naics_6}: non-JSON response (bad key/NAICS/fields?) — first 120 chars: {body[:120]!r}")
        return []

    header, data_rows = rows[0], rows[1:]
    return [dict(zip(header, row)) for row in data_rows]


def fetch(year: int, key: str) -> dict:
    naics_codes = sorted({v["naics_6"] for v in CROSSWALK.values()})
    out: dict[str, dict] = {}

    for naics in naics_codes:
        print(f"Fetching CBP {year}, NAICS {naics} ...")
        for row in _fetch_industry(year, naics, key):
            try:
                estab = int(row["ESTAB"])
                emp = int(row["EMP"])
                payroll_k = int(row["PAYANN"])
            except (KeyError, ValueError):
                continue
            state_fips = row.get("state", "")
            entry = {
                "establishments": estab,
                "employment": emp,
                "annual_payroll_thousands": payroll_k,
                "avg_payroll_per_employee": round(payroll_k * 1000 / emp) if emp else None,
                "year": year,
            }
            out[f"{naics}:{state_fips}"] = entry

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2022, help="CBP vintage year (2022 is latest at time of writing)")
    args = ap.parse_args()

    key = _read_census_key()
    result = fetch(args.year, key)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {len(result)} entries to {OUTPUT_FILE}")
    if not result:
        print("WARNING: nothing written — check the Census key and network access.")
        sys.exit(1)


if __name__ == "__main__":
    main()
