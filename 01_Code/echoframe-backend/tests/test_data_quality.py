"""
Tests for the data-quality gate (B-1) and its review-email surfacing.

Covers:
  • assess(): hard-fails an all-zero money column and a mass row-drop; warns on a
    partly-zero column, dropped rows under the fail threshold, and junk dates;
    stays clean on good data and never raises.
  • review_gate: shows the warnings as a banner on the owner's review copy, and
    STRIPS the internal `_dq_warnings` key before any send reaches a customer.
"""
import os
import pandas as pd

import data_quality


def _df(rows, cols, rows_in=None):
    df = pd.DataFrame(rows, columns=cols)
    if rows_in is not None:
        df.attrs["dq_rows_in"] = rows_in
    return df


# ── assess() ────────────────────────────────────────────────────────────────

def test_clean_data_produces_no_issues():
    df = _df(
        [["2026-05-01", "Deposit", "2300"], ["2026-05-02", "Supplies", "-45"]],
        ["Date", "Description", "Amount"], rows_in=2,
    )
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert not r.hard_fail
    assert r.warnings == []
    assert bool(r) is False


def test_all_zero_money_column_hard_fails():
    # The Rate Watch / Shift Lens failure: a money column that didn't read at all.
    df = _df([["A", "0"], ["B", "0"], ["C", ""]], ["Vendor", "MarketRate"], rows_in=3)
    r = data_quality.assess(df, numeric_cols=["MarketRate"])
    assert r.hard_fail
    assert "MarketRate" in r.reason


def test_mass_row_drop_hard_fails():
    # 40 rows went in, only 12 survived parsing → columns didn't line up.
    df = _df([["2026-05-01", "x", "10"]] * 12, ["Date", "Description", "Amount"], rows_in=40)
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert r.hard_fail
    assert "could not be read" in r.reason


def test_partial_row_drop_warns_but_does_not_fail():
    # 10 in, 8 out (20%) → over warn (15%) but under fail (50%).
    df = _df([["2026-05-01", "x", "10"]] * 8, ["Date", "Description", "Amount"], rows_in=10)
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert not r.hard_fail
    assert any("dropped" in w for w in r.warnings)


def test_junk_dates_warn():
    df = _df(
        [["2026-05-01", "real", "10"],
         ["TBD", "junk", "20"],
         ["32/13/2026", "junk", "30"]],
        ["Date", "Description", "Amount"], rows_in=3,
    )
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert not r.hard_fail
    assert any("Date" in w for w in r.warnings)


def test_unquoted_thousands_overflow_is_flagged():
    # The flagship B-1 bug: "2,300" splits into 2 cells, so one ledger row arrives
    # with more values than columns. df.attrs carries the count from the parser.
    df = _df([["2026-05-01", "Deposit", "2"]], ["Date", "Description", "Amount"], rows_in=1)
    df.attrs["dq_overflow_rows"] = 1
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    # 1 of 1 rows overflowed → over the 30% fail threshold → hard fail.
    assert r.hard_fail
    assert "2,300" in r.reason or "comma" in r.reason


def test_few_overflow_rows_warn_only():
    rows = [["2026-05-01", "ok", "10"]] * 9 + [["2026-05-02", "split", "2"]]
    df = _df(rows, ["Date", "Description", "Amount"], rows_in=10)
    df.attrs["dq_overflow_rows"] = 1  # 10% → warn, not fail
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert not r.hard_fail
    assert any("more values than columns" in w for w in r.warnings)


def test_empty_frame_hard_fails():
    r = data_quality.assess(_df([], ["Date", "Amount"]))
    assert r.hard_fail


def test_assess_never_raises_on_garbage_input():
    # Passing something that isn't a DataFrame must not blow up.
    r = data_quality.assess(None)
    assert r.hard_fail or r.warnings == []


# ── review_gate surfacing + stripping ────────────────────────────────────────

def test_review_banner_shows_warnings():
    import review_gate
    html = review_gate._dq_banner({"_dq_warnings": ["18% of \"Amount\" values are 0 or blank"]})
    assert "Check the data before approving" in html
    assert "Amount" in html
    # No warnings → no banner.
    assert review_gate._dq_banner({}) == ""


def test_dq_warnings_stripped_before_customer_send(monkeypatch):
    """With the gate off (passthrough), `_dq_warnings` must never reach the real send."""
    os.environ["REVIEW_MODE"] = "off"
    import resend
    import review_gate

    captured = {}

    def fake_send(params, *a, **k):
        captured.update(params)
        return {"id": "ok"}

    # Reset any prior install so we wrap our fake as the underlying sender.
    monkeypatch.setattr(resend.Emails, "send", fake_send, raising=False)
    if hasattr(resend.Emails.send, review_gate._INSTALLED_ATTR):
        delattr(resend.Emails.send, review_gate._INSTALLED_ATTR)
    review_gate.install()

    resend.Emails.send({
        "from": "x", "to": ["client@biz.com"], "subject": "Report",
        "html": "<p>hi</p>", "attachments": [{"filename": "r.pdf"}],
        "_dq_warnings": ["some warning"],
    })

    assert "_dq_warnings" not in captured
    assert captured.get("subject") == "Report"
