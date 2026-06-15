from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

def ingest_from_dict(
    raw_transactions: List[Dict[str, Any]],
    raw_punches: List[Dict[str, Any]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert raw transaction and punch data to DataFrames.

    Args:
        raw_transactions: List of dicts with keys: timestamp, amount, order_id, location_id
        raw_punches: List of dicts with keys: employee_id, clock_in, clock_out, wage, location_id

    Returns:
        Tuple of (transactions_df, punches_df)
    """
    txn_df = pd.DataFrame(raw_transactions)
    if not txn_df.empty:
        txn_df["timestamp"] = pd.to_datetime(txn_df["timestamp"])
        txn_df["amount"] = pd.to_numeric(txn_df["amount"])

    punch_df = pd.DataFrame(raw_punches)
    if not punch_df.empty:
        punch_df["clock_in"] = pd.to_datetime(punch_df["clock_in"])
        punch_df["clock_out"] = pd.to_datetime(punch_df["clock_out"])
        punch_df["wage"] = pd.to_numeric(punch_df["wage"])

    return txn_df, punch_df
