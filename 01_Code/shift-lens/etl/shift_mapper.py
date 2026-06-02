from datetime import datetime, date, time, timedelta
from typing import List, Optional
import pandas as pd
from models.shift_definition import ShiftDefinition

class ShiftMapper:
    """Maps POS transactions to shift blocks based on timestamp."""

    def __init__(self, shift_definitions: List[ShiftDefinition]):
        self.shifts = shift_definitions

    def map_transactions_to_shifts(
        self,
        transactions: pd.DataFrame,
        shift_date: date,
        location_id: str
    ) -> pd.DataFrame:
        """
        Map each transaction to the shift it belongs to.

        Transactions are assigned to the nearest shift if no exact match.

        Args:
            transactions: DataFrame with columns [timestamp, amount, order_id]
            shift_date: Date for which to map
            location_id: Location identifier

        Returns:
            DataFrame with columns [transaction_id, amount, shift_definition_id, allocation_pct]
        """
        shifts_for_date = [
            s for s in self.shifts
            if s.location_id == location_id and s.day_of_week == shift_date.weekday()
        ]

        # If no shifts are defined for this day/location, do NOT silently drop the
        # revenue — return every transaction flagged UNALLOCATED so it stays auditable.
        if not shifts_for_date:
            if transactions.empty:
                return pd.DataFrame(
                    columns=["transaction_id", "amount", "shift_definition_id", "allocation_pct"]
                )
            return pd.DataFrame([
                {
                    "transaction_id": row.get("id", idx),
                    "amount": row["amount"],
                    "shift_definition_id": None,
                    "allocation_pct": 0.0,
                }
                for idx, row in transactions.iterrows()
            ])

        results = []
        for idx, row in transactions.iterrows():
            txn_time = row["timestamp"].time()
            best_shift = self._find_nearest_shift(txn_time, shifts_for_date)

            if best_shift:
                results.append({
                    "transaction_id": row.get("id", idx),
                    "amount": row["amount"],
                    "shift_definition_id": best_shift.id,
                    "allocation_pct": 1.0,  # 100% to nearest shift
                })
            else:
                results.append({
                    "transaction_id": row.get("id", idx),
                    "amount": row["amount"],
                    "shift_definition_id": None,
                    "allocation_pct": 0.0,
                })

        return pd.DataFrame(results)

    def _find_nearest_shift(self, txn_time: time, shifts: List[ShiftDefinition]) -> Optional[ShiftDefinition]:
        """
        Find the shift closest to the transaction time.

        Preference: shift that contains the time, then nearest start/end time.
        """
        for shift in shifts:
            if self._time_in_shift(txn_time, shift.start_time, shift.end_time):
                return shift

        min_distance = float("inf")
        nearest_shift = None
        for shift in shifts:
            distance = self._time_distance(txn_time, shift.start_time, shift.end_time)
            if distance < min_distance:
                min_distance = distance
                nearest_shift = shift

        return nearest_shift

    def _time_in_shift(self, txn_time: time, shift_start: time, shift_end: time) -> bool:
        """Check if transaction time falls within shift window."""
        if shift_start < shift_end:
            return shift_start <= txn_time < shift_end
        else:
            return txn_time >= shift_start or txn_time < shift_end

    def _time_distance(self, txn_time: time, shift_start: time, shift_end: time) -> float:
        """Calculate minutes to nearest shift boundary."""
        txn_minutes = txn_time.hour * 60 + txn_time.minute
        start_minutes = shift_start.hour * 60 + shift_start.minute
        end_minutes = shift_end.hour * 60 + shift_end.minute

        if start_minutes < end_minutes:
            if start_minutes <= txn_minutes < end_minutes:
                return 0
            return min(abs(txn_minutes - start_minutes), abs(txn_minutes - end_minutes))
        else:
            if txn_minutes >= start_minutes or txn_minutes < end_minutes:
                return 0
            return min(abs(txn_minutes - start_minutes), abs(txn_minutes - end_minutes))
