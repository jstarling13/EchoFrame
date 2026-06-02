"""Tests for the real Square connector (mocked HTTP — no live calls)."""

from datetime import date

import pytest

import config
from connectors.square import SquarePOS, SquareTimesheet, _SquareClient
from connectors import get_pos_connector


DAY = date(2024, 1, 15)


def test_unavailable_without_token(monkeypatch):
    monkeypatch.setattr(config, "SQUARE_ACCESS_TOKEN", "")
    assert SquarePOS.is_available() is False
    with pytest.raises(RuntimeError):
        SquarePOS().fetch_transactions(DAY, "loc-1")
    # Registry should refuse to hand out an unconfigured Square connector.
    with pytest.raises(ValueError):
        get_pos_connector("square")


def test_pos_normalizes_payments(monkeypatch):
    monkeypatch.setattr(config, "SQUARE_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(config, "TIMEZONE", "UTC")  # keep timestamps stable

    sample = {
        "payments": [
            {"id": "pay_1", "order_id": "ord_1", "status": "COMPLETED",
             "created_at": "2024-01-15T13:30:00Z", "amount_money": {"amount": 4550, "currency": "USD"},
             "source_type": "CARD"},
            {"id": "pay_2", "status": "COMPLETED",
             "created_at": "2024-01-15T18:05:00Z", "amount_money": {"amount": 1200, "currency": "USD"}},
            # Voided payment should be ignored.
            {"id": "pay_3", "status": "FAILED",
             "created_at": "2024-01-15T19:00:00Z", "amount_money": {"amount": 9999}},
        ]
        # no cursor -> single page
    }
    monkeypatch.setattr(_SquareClient, "get", lambda self, path, params: sample)

    txns = SquarePOS().fetch_transactions(DAY, "loc-1")
    assert len(txns) == 2
    assert txns[0]["amount"] == 45.50
    assert txns[0]["order_id"] == "ord_1"
    assert txns[0]["timestamp"].hour == 13
    assert txns[1]["order_id"] == "pay_2"  # falls back to id when no order_id


def test_timesheet_normalizes_shifts(monkeypatch):
    monkeypatch.setattr(config, "SQUARE_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(config, "TIMEZONE", "UTC")

    sample = {
        "shifts": [
            {"team_member_id": "TM-1", "start_at": "2024-01-15T06:00:00Z",
             "end_at": "2024-01-15T14:00:00Z", "wage": {"hourly_rate": {"amount": 1550}}},
            # Open shift (no end_at) should be skipped.
            {"team_member_id": "TM-2", "start_at": "2024-01-15T14:00:00Z"},
        ]
    }
    monkeypatch.setattr(_SquareClient, "post", lambda self, path, body: sample)

    punches = SquareTimesheet().fetch_punches(DAY, "loc-1")
    assert len(punches) == 1
    assert punches[0]["employee_id"] == "TM-1"
    assert punches[0]["wage"] == 15.50
    assert punches[0]["clock_in"].hour == 6
    assert punches[0]["clock_out"].hour == 14


def test_pos_paginates(monkeypatch):
    monkeypatch.setattr(config, "SQUARE_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(config, "TIMEZONE", "UTC")

    pages = [
        {"payments": [{"id": "p1", "status": "COMPLETED",
                       "created_at": "2024-01-15T10:00:00Z", "amount_money": {"amount": 1000}}],
         "cursor": "next"},
        {"payments": [{"id": "p2", "status": "COMPLETED",
                       "created_at": "2024-01-15T11:00:00Z", "amount_money": {"amount": 2000}}]},
    ]
    calls = {"n": 0}

    def fake_get(self, path, params):
        page = pages[calls["n"]]
        calls["n"] += 1
        return page

    monkeypatch.setattr(_SquareClient, "get", fake_get)
    txns = SquarePOS().fetch_transactions(DAY, "loc-1")
    assert [t["order_id"] for t in txns] == ["p1", "p2"]
    assert calls["n"] == 2
