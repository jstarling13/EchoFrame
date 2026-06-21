"""
Robustness tests — messy real-world CSVs must never crash an engine.

Covers the shared csv_utils reader/parsers and the Clarity loader (the one that
used to blow up with a raw pandas traceback on a non-financials / jagged file).
"""
from pathlib import Path

import pytest

import csv_utils


def test_to_amount_handles_messy_money():
    assert csv_utils.to_amount("$4,500.00") == 4500.0
    assert csv_utils.to_amount("4500") == 4500.0
    assert csv_utils.to_amount("$4500") == 4500.0
    assert csv_utils.to_amount("(1,200)") == -1200.0     # parens = negative
    assert csv_utils.to_amount("  $ 9,600  ") == 9600.0
    assert csv_utils.to_amount("") == 0.0
    assert csv_utils.to_amount(None) == 0.0
    assert csv_utils.to_amount("John Smith") == 0.0      # non-numeric → 0, never raises


def test_read_rows_tolerates_bom_jagged_and_blank():
    raw = ("﻿_Business Name,Acme\nRevenue,42000\nA,B,C,D,E\n\n,,\n").encode("utf-8")
    rows = csv_utils.read_rows(raw)
    assert rows[0][0] == "_Business Name"                # BOM stripped
    assert ["A", "B", "C", "D", "E"] in rows             # wide jagged row preserved, no crash


def test_read_rows_handles_semicolons_and_bad_encoding():
    # semicolon-delimited, latin-1 byte that isn't valid utf-8
    raw = b"_Month;May\nRevenue;42000\nCaf\xe9;1200\n"
    rows = csv_utils.read_rows(raw)
    meta, data = csv_utils.split_meta(rows)
    assert meta.get("Month") == "May"
    assert any(r and r[0] == "Revenue" for r in data)


def test_split_meta_separates_header_rows():
    rows = [["_Month", "May"], ["Revenue", "42000"], ["", ""], ["Rent", "3200"]]
    meta, data = csv_utils.split_meta(rows)
    assert meta["Month"] == "May"
    assert ["Revenue", "42000"] in data and ["Rent", "3200"] in data
    assert ["", ""] not in data                          # blank rows dropped


def test_clarity_loader_does_not_crash_on_quote_data():
    from products.clarity import clarity_engine as ce
    quote_csv = ("_Business Name,X\n"
                 "Quote ID,customer_name,Contact Email,quote_amount,STATUS,notes\n"
                 "Q-1001,John Smith,john@x.com,\"$4,500.00\",Sent,\n")
    safe = ce._safe_email("badfin@test.local")
    Path(ce.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    p = Path(ce.UPLOADS_DIR) / f"{safe}.csv"
    p.write_text(quote_csv, encoding="utf-8")
    try:
        with pytest.raises(ValueError):                  # clean rejection, NOT a pandas ParserError
            ce._load_financials("badfin@test.local")
    finally:
        p.unlink(missing_ok=True)


def test_clarity_loader_parses_messy_but_valid_financials():
    from products.clarity import clarity_engine as ce
    messy = ('﻿_Business Name,Reliable Heating\n_Month,May 2026\n'
             'Revenue ,"$42,000.00", 38000\n Food Cost ,13500,12800\n\n,,\nMarketing,(1200),900\n')
    safe = ce._safe_email("okfin@test.local")
    Path(ce.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    p = Path(ce.UPLOADS_DIR) / f"{safe}.csv"
    p.write_text(messy, encoding="utf-8")
    try:
        df, meta = ce._load_financials("okfin@test.local")
        assert meta.get("Business Name") == "Reliable Heating"
        rev = df[df[0].str.lower() == "revenue"]["Current"].iloc[0]
        mkt = df[df[0].str.lower() == "marketing"]["Current"].iloc[0]
        assert rev == 42000.0
        assert mkt == -1200.0
    finally:
        p.unlink(missing_ok=True)


# Every report engine must survive a messy upload: a UTF-8 BOM, Windows-1252
# smart quotes (byte 0x92, invalid UTF-8), and ANNOTATED/renamed headers that the
# old exact-match check would have rejected. (module, loader_fn, csv-body) — the
# loader must return non-empty data without raising.
_ENGINE_CASES = [
    ("products.auto_ledger.auto_ledger_engine", "load_ledger_path",
     "_Business Name,Test\nDate,Description,Amount (USD),Account #\n2026-05-01,Fuel \x92stop,-120.50,Operating\n"),
    ("products.bay_coach.bay_coach_engine", "load_path",
     "_Shop,Test\nService Performed,When\nOil change,2026-01-10\nService,Interval,Status,Price ($)\nBrake \x92flush,30000 mi,Overdue,189\n"),
    ("products.business_audit.business_audit_engine", "load_path",
     "_Business Name,Joe\x92s\nMonth,Revenue ($),Expenses\nJan,12000,8000\nFeb,13500,8200\n"),
    ("products.call_catch.call_catch_engine", "load_path",
     "_Business Name,Test\nTime,AutoText,Outcome\n2:15 PM,Yes we\x92ll book,won 740\n"),
    ("products.call_router.call_router_engine", "load_path",
     "_Business Name,Test\nTime,Customer Need,Qualification?\n9am,New \x92roof,Qualified\n"),
    ("products.clear_ledger.clear_ledger_engine", "load_path",
     "_Business Name,Test\nCustomer Name,Invoice #,Amount\nBob\x92s Diner,INV-1,4500\n"),
    ("products.competitor_landscape.competitor_landscape_engine", "load_path",
     "_Business Name,Test\nCompetitor Name,Description (notes)\nJoe\x92s Garage,Cheap and fast\n"),
    ("products.crew_hire.crew_hire_engine", "load_path",
     "_Business Name,Test\nCandidate Name,Score /100,Status\nJane O\x92Brien,88,Interview\n"),
    ("products.drive_pay.drive_pay_engine", "load_path",
     "_Business Name,Test\nTime,Invoice #,Outcome\n10am,RO-1,Paid \x92won\n"),
    ("products.permit_watch.permit_watch_engine", "load_path",
     "_Business Name,Test\nItem Name,Entity,Expiry Date\nTruck\x92s Reg,Fleet,2026-08-01\n"),
    ("products.rate_watch.rate_watch_engine", "load_vendors_path",
     "_Business Name,Test\nVendor,Current Rate (%),Market Rate\nACME\x92s,12.5,9.0\n"),
    ("products.rival_scan.rival_scan_engine", "load_rivals_path",
     "_Business Name,Test\nCompetitor,Key Price ($),Rating /5\nTony\x92s Oven,15.99,4.5\n"),
    ("products.shift_lens.shift_lens_engine", "load_shifts_path",
     "_Business Name,Test\nDay,Revenue,Labor Cost ($)\nMon\x92Fri,4620,1010\n"),
]


@pytest.mark.parametrize("module,fn,body", _ENGINE_CASES,
                         ids=[c[0].split(".")[-1] for c in _ENGINE_CASES])
def test_every_engine_reads_a_messy_upload(module, fn, body, tmp_path):
    import importlib
    eng = importlib.import_module(module)
    raw = b"\xef\xbb\xbf" + body.encode("latin-1")   # UTF-8 BOM + cp1252 smart quote
    p = tmp_path / "messy.csv"
    p.write_bytes(raw)
    res = getattr(eng, fn)(p)                          # must not raise on bad bytes
    df = res[0] if isinstance(res, (tuple, list)) else res
    assert df is not None and len(df) > 0, f"{module} couldn't read the messy upload"


def test_quote_revive_typo_flag_is_scale_relative():
    """Typo detection depends on the company's OWN numbers, never a fixed dollar cap."""
    from products.quote_revive import quote_revive_engine as qr
    # One absurd sentinel among a normal book → only it is flagged; the legit $250k is not.
    flags = qr._flag_suspects([500, 1500, 15000, 250000, 9999999999])
    assert flags == [False, False, False, False, True]
    # A six-figure quote for a seven-figure-scale shop → NOT flagged (the whole point).
    assert qr._flag_suspects([40000, 80000, 120000, 150000, 200000]) == [False] * 5
    # A small shop's one genuinely large job stays in-range relative to the rest.
    assert qr._flag_suspects([500, 800, 1200, 9000]) == [False] * 4
    # Too few quotes to judge an outlier → never flag.
    assert qr._flag_suspects([100, 9999999999]) == [False, False]


def test_quote_revive_parses_real_world_headers():
    """A customer's actual export won't use our sample column names — map by meaning,
    derive 'days cold' from a date, and tolerate a mid-file BOM, $ and commas, mixed
    status words. This is the file shape that returned 0 quotes before."""
    from products.quote_revive import quote_revive_engine as qr
    messy = ("_Business Name,Bayside Plumbing\n"
             "﻿Quote ID,customer_name,Contact Email,Job Description,quote_amount,Date Sent,STATUS,notes\n"
             "Q-1001,John Smith,john@x.com,Drain cleaning,\"$4,500.00\",2026-05-01,Sent,\n"
             "Q-1002,Jane Roe,jane@x.com,Water heater,\"$3,200\",05/02/2026,Replied,\n"
             "Q-1003,,,Whole-home repipe,9400,2026-04-15,Closed Won,\n"
             "\n,,,,,,,\n")
    safe = qr._safe_email("realworld@test.local")
    Path(qr.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    p = Path(qr.UPLOADS_DIR) / f"{safe}.csv"
    p.write_text(messy, encoding="utf-8")
    try:
        df, meta = qr.load_path(p)
        assert df is not None and len(df) == 3            # 3 real rows, blank row dropped
        assert meta.get("Business Name") == "Bayside Plumbing"
        assert set(df["ValueNum"]) == {4500.0, 3200.0, 9400.0}   # $ and commas parsed
        keys = set(df["StatusKey"])
        assert "active" in keys and "warm" in keys and "won" in keys  # Sent/Replied/Closed Won
        assert bool(df["Dated"].any())                    # days came from the date column
    finally:
        p.unlink(missing_ok=True)
