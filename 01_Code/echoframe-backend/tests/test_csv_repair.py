"""
Tests for csv_utils.repair_overflow_row — the Step-2 fix for unquoted thousands
separators ("2,300" split into "2" + "300" by the CSV reader).

The contract: repair ONLY the unambiguous comma-split-number case, and only when
the row is over-wide. If it can't land exactly on ncols, return the row untouched
so the data-quality gate handles it. Never "repair" into a different wrong number.
"""
import csv_utils as cu


# ── the cases we DO repair ───────────────────────────────────────────────────

def test_simple_thousands_split():
    # "2026-05-01,Customer deposit,2,300,Checking" → amount column was split.
    row = ["2026-05-01", "Customer deposit", "2", "300", "Checking"]
    assert cu.repair_overflow_row(row, 4) == ["2026-05-01", "Customer deposit", "2300", "Checking"]


def test_millions_two_commas():
    row = ["x", "1", "234", "567", "y"]
    assert cu.repair_overflow_row(row, 3) == ["x", "1234567", "y"]


def test_decimal_tail_on_last_group():
    row = ["x", "2", "300.50", "y"]
    assert cu.repair_overflow_row(row, 3) == ["x", "2300.50", "y"]


def test_negative_parens_split():
    # "(1,200)" → "(1" + "200)"
    row = ["x", "(1", "200)", "y"]
    assert cu.repair_overflow_row(row, 3) == ["x", "(1200)", "y"]


def test_dollar_prefix_split():
    row = ["x", "$2", "300", "y"]
    assert cu.repair_overflow_row(row, 3) == ["x", "$2300", "y"]


def test_repaired_amount_parses_correctly():
    row = ["2026-05-01", "Deposit", "2", "300", "Checking"]
    fixed = cu.repair_overflow_row(row, 4)
    assert cu.to_amount(fixed[2]) == 2300.0   # the whole point: $2,300 not $2


# ── the cases we must NOT touch ──────────────────────────────────────────────

def test_correct_width_row_untouched():
    row = ["2026-05-01", "Deposit", "2300", "Checking"]
    assert cu.repair_overflow_row(row, 4) == row


def test_non_numeric_extra_field_not_merged():
    # A real extra junk column is NOT a split number → leave it for the gate.
    row = ["a", "b", "c", "d", "e"]
    assert cu.repair_overflow_row(row, 4) == row


def test_trailing_text_after_split_is_left_for_gate():
    # Split number AND trailing junk → can't land cleanly → untouched.
    row = ["2026-05-01", "desc", "2", "300", "Checking", "JUNK"]
    assert cu.repair_overflow_row(row, 4) == row


def test_two_digit_neighbour_not_merged():
    # "45","67" is not a thousands split (67 is not a 3-digit group).
    row = ["x", "45", "67", "y"]
    assert cu.repair_overflow_row(row, 3) == row


def test_year_like_lead_not_merged():
    # 2024 is 4 digits, not a 1-3 digit lead, so it must NOT swallow "500" into
    # "2024500". Over-wide (2 cells, ncols 1) but unrepairable → returned as-is.
    row = ["2024", "500"]
    assert cu.repair_overflow_row(row, 1) == ["2024", "500"]
