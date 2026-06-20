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


def _norm_cell(c) -> str:
    """Lowercase, strip punctuation to spaces, collapse — for header matching."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(c or "").lower())).strip()


def header_matches(cells: list[str], tokens, quorum: int | None = None) -> bool:
    """True if a row plausibly IS the wanted header. Tolerant: each token need only
    appear as a whole word inside some cell, so 'invoice' matches 'Invoice #',
    'customer' matches 'Customer Name', 'current rate' matches 'Current Rate (%)'.

    Matches when at least `quorum` tokens are found (default: all of them). This
    replaces the brittle `set.issubset(exact-lowercased-cells)` check that broke the
    moment a client renamed or annotated a column."""
    norm_cells = [_norm_cell(c) for c in cells]
    want = [_norm_cell(t) for t in tokens]
    found = 0
    for t in want:
        tw = t.split()
        if tw and any(all(w in nc.split() for w in tw) for nc in norm_cells):
            found += 1
    need = quorum if quorum is not None else len(want)
    return found >= need


def find_header(rows: list[list[str]], tokens, quorum: int | None = None, limit: int = 40) -> int:
    """Index of the first row that looks like the wanted header, or -1 if none."""
    for i, row in enumerate(rows[:limit]):
        if header_matches(row, tokens, quorum):
            return i
    return -1


def cell(row: list[str], i: int, default: str = "") -> str:
    """Safe indexed access into a (possibly short) row."""
    return row[i].strip() if row and i < len(row) and row[i] is not None else default


# ── repairing comma-split numbers (the unquoted-thousands bug) ───────────────
# A value like 2,300 written WITHOUT quotes (exactly how QuickBooks exports it)
# gets split on its own thousands comma by any CSV reader: one cell "2,300"
# becomes two cells "2" and "300". The row then has more cells than the header
# has columns, and the amount reads as $2. These patterns let us re-join ONLY the
# unambiguous case — a 1-3 digit lead followed by exactly-3-digit groups (with an
# optional decimal/closing-paren tail on the last group). Anything else is left
# alone for the data-quality gate to flag, so we never "repair" one wrong number
# into a different wrong number.
_NUM_LEAD = re.compile(r"^[(\-]?\$?\d{1,3}$")     # 12  -12  (1  $250
_NUM_MID = re.compile(r"^\d{3}$")                 # interior thousands group: 234
_NUM_END = re.compile(r"^\d{3}(\.\d+)?\)?$")      # final group: 300  300.00  200)


def _merge_thousands(cells: list[str]) -> tuple[list[str], bool]:
    """Merge the FIRST comma-split number found in `cells`. Returns (cells, merged?)."""
    n = len(cells)
    for i in range(n - 1):
        if not _NUM_LEAD.match(cells[i]):
            continue
        j = i + 1
        while j < n and _NUM_MID.match(cells[j]):       # consume interior 3-digit groups
            j += 1
        end = j
        if j < n and _NUM_END.match(cells[j]) and not _NUM_MID.match(cells[j]):
            end = j + 1                                  # absorb a decimal/paren final group
        if end - i >= 2:                                 # lead + at least one group
            return cells[:i] + ["".join(cells[i:end])] + cells[end:], True
    return cells, False


def repair_overflow_row(row, ncols: int):
    """Re-join an over-wide row whose extra cells are a comma-split number.

    Only applies when the row has MORE cells than `ncols` (i.e. it's already
    broken). Merges unambiguous thousands-groups until the row lands exactly on
    `ncols`; if it can't reach `ncols` cleanly, the ORIGINAL row is returned
    untouched (the data-quality gate will then flag it). Never raises."""
    if not row or ncols <= 0 or len(row) <= ncols:
        return row
    try:
        cells = [str(c).strip() for c in row]
        changed = True
        while len(cells) > ncols and changed:
            cells, changed = _merge_thousands(cells)
        return cells if len(cells) == ncols else row
    except Exception:
        return row


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
