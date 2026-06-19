"""
EchoFrame — robust CSV reading for messy real-world client exports
─────────────────────────────────────────────────────────────────────────────
Clients export from QuickBooks, Jobber, Excel, Google Sheets, you name it — and
the files are sloppy: byte-order marks, the wrong encoding, semicolons instead of
commas, jagged rows (every line a different width), "$4,500.00" next to "4500",
blank lines, stray quotes. None of that should ever crash a report engine.

Everything here is built to NEVER raise on malformed input — worst case it returns
empty/zero and the caller decides what to do. Use read_rows() to parse, split_meta()
to peel off the EchoFrame `_Key,value` header rows, and to_amount() to read money.
"""

from __future__ import annotations

import csv
import io
import re

_BOM = "﻿"
_AMOUNT_STRIP = re.compile(r"[^0-9.\-]")


def decode_bytes(raw) -> str:
    """Decode bytes to text, trying the encodings real exports actually use."""
    if isinstance(raw, str):
        return raw
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    return raw.decode("latin-1", "replace")


def _sniff_delimiter(text: str) -> str:
    """Best-effort delimiter detection — comma, semicolon, tab, or pipe."""
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except Exception:
        counts = {d: sample.count(d) for d in (",", ";", "\t", "|")}
        best = max(counts, key=counts.get)
        return best if counts[best] else ","


def read_rows(raw) -> list[list[str]]:
    """Parse any CSV-ish blob into a list of rows (each a list of clean strings).

    Tolerates BOMs, encoding, mixed delimiters, jagged rows and stray quotes, and
    NEVER raises — on total failure it falls back to a naive split, then to []."""
    text = decode_bytes(raw)
    if not text or not text.strip():
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    delim = _sniff_delimiter(text)
    rows: list[list[str]] = []
    try:
        for row in csv.reader(io.StringIO(text), delimiter=delim):
            rows.append([(c or "").replace(_BOM, "").strip() for c in row])
    except Exception:
        for line in text.split("\n"):
            rows.append([c.replace(_BOM, "").strip() for c in line.split(delim)])
    return rows


def split_meta(rows: list[list[str]]) -> tuple[dict, list[list[str]]]:
    """Peel the EchoFrame `_Key,value` meta rows off the top from the data rows.

    Blank rows are dropped. Meta may appear anywhere; data is everything else."""
    meta: dict = {}
    data: list[list[str]] = []
    for row in rows:
        if not row or not any((c or "").strip() for c in row):
            continue
        first = (row[0] or "").strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = (row[1].strip() if len(row) > 1 else "")
        else:
            data.append(row)
    return meta, data


def cell(row: list[str], i: int, default: str = "") -> str:
    """Safe indexed access into a (possibly short) row."""
    return row[i].strip() if row and i < len(row) and row[i] is not None else default


def to_amount(value) -> float:
    """Parse a money/number cell as tolerantly as possible.

    Handles "$4,500.00", "4500", "$4500", "(1,200)" (parens = negative), trailing
    text, and whitespace. Returns 0.0 for anything unparseable — never raises."""
    if value is None:
        return 0.0
    t = str(value).strip()
    if not t:
        return 0.0
    negative = t.startswith("(") and t.endswith(")")
    t = _AMOUNT_STRIP.sub("", t)
    # collapse a stray second dot (e.g. thousands written as "1.234.56")
    if t.count(".") > 1:
        head, _, tail = t.rpartition(".")
        t = head.replace(".", "") + "." + tail
    if t in ("", "-", ".", "-.", "."):
        return 0.0
    try:
        v = float(t)
    except ValueError:
        return 0.0
    return -v if negative else v
