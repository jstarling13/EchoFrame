"""
EchoFrame data-quality gate
─────────────────────────────────────────────────────────────────────────────
The other safety nets answer "did we send *something*?":

  • email_failsafe   — delivery failed (Resend refused) → bounce to owner.
  • fulfillment_guard — engine produced NOTHING → reassure customer, alert owner.
  • review_gate       — hold every report for a human "Approve & send" click.

None of them answer the question that B-1 of the QA audit is about: *was the
customer's file actually read correctly?* A messy export can sail through every
net above and produce a polished, "complete" report built on wrong numbers — a
$2,300 deposit read as $2, a $0 market rate that invents a huge fake overpayment,
literal junk rows ("EXTRA", "TBD", "32/13/2026") rendered as real data. The
report LOOKS clean, so a human skimming the review copy won't catch it either.

This module compares what went IN against what came OUT and reports honestly:

  • hard_fail = True  → the data is too broken to trust. The engine should return
    "" so the EXISTING fulfillment_guard path fires (customer gets the calm "a
    human is finishing it" note; owner gets the file to do by hand).
  • warnings = [...]   → the report was produced but the file looked off. The
    engine passes these into its send; review_gate stamps them as a banner on the
    owner's "Approve & send" email, so the reviewer knows exactly what to check
    before releasing it to the customer.

Like the other guards, assess() NEVER raises — a gate that throws would defeat
its own purpose. On any internal error it returns a clean (no-issue) result so it
can only ever *add* protection, never block a good report.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

# Per-request stash of the friendly, customer-safe message for the LAST hard fail
# seen on this thread. The fulfilment runner resets it before each report and reads
# it after, so a gate hard-fail can show the customer a helpful note (B-5) without
# every engine having to raise — they still just `return ""` on hard_fail.
_scope = threading.local()

# A safe, generic line for ANY data-quality hard fail. Deliberately non-technical
# (the precise reason goes to the owner, not the customer).
_HARD_FAIL_CUSTOMER_MSG = (
    "We couldn't read your file reliably — some rows didn't line up the way we "
    "expected. Please re-export it as a CSV (avoid merged cells or extra header "
    "rows) and upload it again. If it keeps happening, just reply to this email "
    "and Jacob will finish it by hand."
)


def reset() -> None:
    """Clear the per-request hard-fail message (call once before generating)."""
    _scope.customer_message = ""


def last_customer_message() -> str:
    """The customer-safe message for the most recent hard fail this request, if any."""
    return getattr(_scope, "customer_message", "") or ""


def customer_message_for(reason: str = "") -> str:
    """The customer-safe message for a data-quality hard fail (reason unused for
    now; kept so the wording can specialize later without touching callers)."""
    return _HARD_FAIL_CUSTOMER_MSG


def _hard(result):
    """Finalize a hard-fail result, stashing its customer-safe message for the
    fulfilment runner to surface to the customer (B-5)."""
    try:
        _scope.customer_message = customer_message_for(result.reason)
    except Exception:
        pass
    return result

# Date formats real exports actually use. Used only to tell a plausible date from
# obvious junk ("soon", "TBD", "32/13/2026") — not to reformat anything.
_DATE_FORMATS = (
    "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y",
    "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y",
)


def looks_like_date(value) -> bool:
    """True if value parses as a calendar date in any common export format."""
    t = str(value or "").strip()
    if not t:
        return False
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(t, fmt)
            return True
        except ValueError:
            continue
    return False


@dataclass
class DQResult:
    """Outcome of a data-quality assessment.

    Truthy when there is anything worth surfacing (a warning or a hard fail).
    """
    label: str = "report"
    warnings: list[str] = field(default_factory=list)
    hard_fail: bool = False
    reason: str = ""

    def __bool__(self) -> bool:
        return bool(self.warnings or self.hard_fail)

    def banner_lines(self) -> list[str]:
        """All lines worth showing the reviewer (hard reason first, if any)."""
        lines: list[str] = []
        if self.hard_fail and self.reason:
            lines.append(self.reason)
        lines.extend(self.warnings)
        return lines


def discrepancy_note(label, reported, computed, *, is_money: bool = False,
                     frac: float | None = None):
    """For the meta-passthrough products (B-2): when a customer TYPED a headline
    number that the uploaded data can also compute, compare them and return a
    short owner-facing note if they disagree materially — else None.

    We keep the customer's typed value (it may be the truer one — the data export
    can be partial), but this surfaces the gap on the review email so the owner
    isn't unknowingly sending a number the data contradicts. Never raises."""
    try:
        if computed is None or reported is None:
            return None
        reported = float(reported)
        computed = float(computed)
        f = frac if frac is not None else (0.02 if is_money else 0.05)
        tol = max(1.0, f * abs(computed))
        if abs(reported - computed) <= tol:
            return None
        fmt = (lambda v: f"${v:,.0f}") if is_money else (lambda v: f"{v:g}")
        return (f"{label}: you reported {fmt(reported)}, but the uploaded data "
                f"shows {fmt(computed)} — sending the reported figure.")
    except Exception:
        return None


def is_severe_overstatement(reported, computed, factor: float = 10.0) -> bool:
    """True when a customer-TYPED figure dwarfs what the uploaded data shows by at
    least `factor` (an order-of-magnitude gap, e.g. typed $90,000 vs data $500).
    Such a report shouldn't be one-click-approvable — the engine routes it to the
    manual/owner path instead (E-1). Never raises."""
    try:
        r, c = float(reported), float(computed)
        return r >= factor * max(c, 1.0) and (r - c) > 100
    except Exception:
        return False


def clamp_pct(value, lo: int = 0, hi: int = 150):
    """Clamp a percentage into a sane range so a typed/derived figure can't print an
    absurd value like 7500%. The ceiling is 150 (not 100) on purpose: a real month can
    legitimately exceed 100% — e.g. revenue reactivated above the month-start pipeline
    because new quotes arrived mid-month — so we bound only the truly absurd. Returns an
    int. Never raises."""
    try:
        v = int(round(float(value)))
        return max(lo, min(hi, v))
    except Exception:
        return lo


def _coerce_numeric_series(series):
    import pandas as pd
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True),
        errors="coerce",
    )


def assess(
    df,
    *,
    rows_in: int | None = None,
    overflow_rows: int | None = None,
    numeric_cols=(),
    date_cols=(),
    label: str = "report",
    drop_warn: float = 0.15,
    drop_fail: float = 0.50,
    zero_warn: float = 0.80,
    overflow_fail: float = 0.30,
) -> DQResult:
    """Compare a parsed DataFrame against the file it came from and flag trouble.

    Args:
      df          — the engine's FINAL parsed table (a pandas DataFrame).
      rows_in     — count of data rows the parser SAW before filtering (optional
                    but strongly recommended; df.attrs['dq_rows_in'] is read as a
                    fallback). Lets us catch rows silently dropped or mis-split.
      numeric_cols— money/number columns that should mostly be non-zero. An
                    all-zero column means it wasn't read (e.g. "market rate").
      date_cols   — columns that should hold real dates. Junk here = junk rows.
      drop_warn/drop_fail — fraction of input rows lost that triggers warn/fail.
      zero_warn   — fraction of a numeric column that is 0/blank to warn about.

    Returns a DQResult. Never raises.
    """
    result = DQResult(label=label)
    try:
        rows_out = int(len(df)) if df is not None else 0

        # 0) No usable rows at all → hard fail. (Belt-and-suspenders: most engines
        #    already return "" here, but a gate should never assume.)
        if rows_out == 0:
            result.hard_fail = True
            result.reason = "No usable rows could be read from the uploaded file."
            return _hard(result)

        # 1) Rows that went in but didn't come out → silently dropped or mis-split.
        if rows_in is None and df is not None:
            rows_in = df.attrs.get("dq_rows_in")
        if rows_in:
            rows_in = int(rows_in)
            if rows_in > 0 and rows_out < rows_in:
                dropped = rows_in - rows_out
                frac = dropped / rows_in
                if frac >= drop_fail:
                    result.hard_fail = True
                    result.reason = (
                        f"{dropped} of {rows_in} rows ({frac:.0%}) could not be read "
                        f"— the file's columns likely didn't line up."
                    )
                    return _hard(result)
                if frac >= drop_warn:
                    result.warnings.append(
                        f"{dropped} of {rows_in} rows ({frac:.0%}) were dropped during "
                        f"parsing — some lines may be missing from this report."
                    )

        # 1b) Rows with MORE cells than columns = the unquoted-thousands signature
        #     ("2,300" → "2" + "300"). The amount on those rows is almost certainly
        #     wrong, so this is the single most important signal for B-1.
        if overflow_rows is None and df is not None:
            overflow_rows = df.attrs.get("dq_overflow_rows")
        if overflow_rows:
            overflow_rows = int(overflow_rows)
            frac = overflow_rows / rows_out if rows_out else 1.0
            msg = (
                f"{overflow_rows} row(s) had more values than columns — either a "
                f'value with a comma (e.g. an unquoted "2,300" splitting into 2 + 300, '
                f"which mis-reads the amount) or stray junk fields. The data on these "
                f"rows is likely shifted/wrong — verify them."
            )
            if frac >= overflow_fail:
                result.hard_fail = True
                result.reason = msg
                return _hard(result)
            result.warnings.append(msg)

        # 2) Numeric columns that are entirely / mostly zero → column wasn't read.
        for col in numeric_cols:
            if df is None or col not in getattr(df, "columns", []):
                continue
            nums = _coerce_numeric_series(df[col])
            zero_or_blank = (nums.isna() | (nums == 0)).mean()
            if zero_or_blank >= 1.0:
                result.hard_fail = True
                result.reason = (
                    f'Every value in "{col}" read as 0 — that column was almost '
                    f"certainly not read from the file."
                )
                return _hard(result)
            if zero_or_blank >= zero_warn:
                pct = int(round(zero_or_blank * 100))
                result.warnings.append(
                    f'{pct}% of "{col}" values are 0 or blank — double-check that '
                    f"column came through correctly."
                )

        # 3) Date columns full of non-dates → junk rows leaking in as real data.
        for col in date_cols:
            if df is None or col not in getattr(df, "columns", []):
                continue
            bad = sum(0 if looks_like_date(v) else 1 for v in df[col])
            if bad:
                frac = bad / rows_out
                if frac >= 0.5:
                    result.warnings.append(
                        f'{bad} of {rows_out} rows have an unreadable "{col}" '
                        f"(e.g. junk like \"TBD\" or an invalid date) — they may "
                        f"not be real entries."
                    )
                elif bad:
                    result.warnings.append(
                        f'{bad} row(s) have an unreadable "{col}" value and may be junk.'
                    )

        return result
    except Exception as exc:  # a gate must never block a good report
        return DQResult(label=label, warnings=[], hard_fail=False,
                        reason=f"(data-quality check skipped: {type(exc).__name__})")
