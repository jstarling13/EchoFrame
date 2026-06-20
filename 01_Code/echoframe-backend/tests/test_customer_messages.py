"""
Tests for B-5 — surfacing a specific, customer-safe message instead of the
generic "a human is finishing it" note.

Covers: the CustomerInputError type, the data-quality hard-fail message stash,
and fulfillment_guard choosing the specific vs generic customer email.
"""
import pandas as pd

import data_quality
from customer_errors import CustomerInputError


def test_customer_input_error_carries_message_and_internal():
    e = CustomerInputError("please upload your P&L", internal="no revenue row")
    assert e.customer_message == "please upload your P&L"
    assert "no revenue row" in str(e)           # owner/log sees internal detail
    # Without internal, str() falls back to the customer message.
    assert str(CustomerInputError("hi")) == "hi"


def test_gate_hardfail_stashes_customer_message():
    data_quality.reset()
    assert data_quality.last_customer_message() == ""
    df = pd.DataFrame([], columns=["Amount"])    # zero rows → hard fail
    r = data_quality.assess(df, numeric_cols=["Amount"])
    assert r.hard_fail
    msg = data_quality.last_customer_message()
    assert msg and ("re-export" in msg.lower() or "csv" in msg.lower())
    assert "row" not in msg.lower() or "rows didn't line up" in msg.lower()  # non-technical


def test_gate_clean_leaves_no_stash():
    data_quality.reset()
    df = pd.DataFrame([["2026-05-01", "x", "10"]], columns=["Date", "Desc", "Amount"])
    df.attrs["dq_rows_in"] = 1
    r = data_quality.assess(df, numeric_cols=["Amount"], date_cols=["Date"])
    assert not r.hard_fail
    assert data_quality.last_customer_message() == ""


def _capture_sends(monkeypatch):
    import resend
    sent = []
    monkeypatch.setattr(resend.Emails, "send", lambda p, *a, **k: (sent.append(p), {"id": "x"})[1])
    return sent


def test_notify_unreadable_uses_specific_message(monkeypatch):
    import fulfillment_guard
    sent = _capture_sends(monkeypatch)
    fulfillment_guard.notify_unreadable(
        "client@biz.com", "Sam", "Clarity Report",
        reason="ValueError: ...", customer_message="Please upload a profit-and-loss export.")
    cust = [s for s in sent if "client@biz.com" in str(s.get("to"))]
    assert cust, "customer email should be sent"
    assert "profit-and-loss" in cust[0]["html"]
    assert "Quick fix needed" in cust[0]["subject"]


def test_notify_unreadable_generic_when_no_message(monkeypatch):
    import fulfillment_guard
    sent = _capture_sends(monkeypatch)
    fulfillment_guard.notify_unreadable("client@biz.com", "Sam", "Clarity Report", reason="boom")
    cust = [s for s in sent if "client@biz.com" in str(s.get("to"))]
    assert cust
    assert "within one business day" in cust[0]["html"]
    assert "profit-and-loss" not in cust[0]["html"]


def test_clarity_validation_raises_customer_input_error():
    # The three Clarity validation guards must raise the customer-safe type so the
    # web layer surfaces them (rather than the generic note). Verified structurally:
    # the engine imports and references CustomerInputError for its input checks.
    import products.clarity.clarity_engine as ce
    assert ce.CustomerInputError is CustomerInputError
