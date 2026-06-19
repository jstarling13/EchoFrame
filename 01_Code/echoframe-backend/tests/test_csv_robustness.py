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
