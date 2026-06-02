"""Mock Square/Toast-style POS connector.

Generates deterministic-but-realistic transactions for a given day so the
end-to-end pipeline can be exercised without a live POS account. Output shape
matches what a real Square 'list payments' pull would be normalized into.
"""

import random
from datetime import date, datetime, time
from typing import List, Dict, Any

from connectors.base import POSConnector
from logging_config import get_logger

logger = get_logger("connector.pos")

# Business hours used to scatter transactions across the day.
_OPEN_HOUR = 6
_CLOSE_HOUR = 22


class MockSquarePOS(POSConnector):
    name = "mock_square"

    def fetch_transactions(self, day: date, location_id: str) -> List[Dict[str, Any]]:
        # Seed by date+location so repeated pulls of the same day are stable.
        rng = random.Random(hash((day.toordinal(), location_id)) & 0xFFFFFFFF)
        is_weekend = day.weekday() >= 5

        transactions: List[Dict[str, Any]] = []
        seq = 1
        for hour in range(_OPEN_HOUR, _CLOSE_HOUR):
            # Lunch (11-13) and dinner (17-20) rushes; weekends busier.
            if hour in (11, 12, 17, 18, 19):
                base = 6
            elif 13 <= hour <= 16:
                base = 3
            else:
                base = 2
            count = int(base * (1.4 if is_weekend else 1.0))
            for _ in range(count):
                ts = datetime.combine(day, time(hour, rng.randint(0, 59)))
                amount = round(rng.uniform(7.5, 72.0), 2)
                transactions.append({
                    "timestamp": ts,
                    "amount": amount,
                    "order_id": f"SQ-{day.isoformat()}-{seq:04d}",
                    "location_id": location_id,
                    "payment_method": rng.choice(["card", "card", "card", "cash"]),
                })
                seq += 1

        transactions.sort(key=lambda t: t["timestamp"])
        logger.info("MockSquarePOS pulled %d transactions for %s @ %s",
                    len(transactions), day, location_id)
        return transactions
