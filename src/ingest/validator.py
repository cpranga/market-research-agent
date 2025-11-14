from typing import List, Set, Tuple
from datetime import datetime, timezone, timedelta
import math

from ingest.providers.base import TradeRecord

def validate(records: List[TradeRecord]) -> List[TradeRecord]:
    val_records: List[TradeRecord] = []
    seen_records: Set[Tuple[str, datetime]] = set()
    tolerance = timedelta(seconds=10)

    if not records:
        return []

    for record in records:
        # Type check
        if not isinstance(record, TradeRecord):
            raise ValueError("Not a TradeRecord: {}".format(record))

        # Fix what we can in the records
        record.symbol = record.symbol.strip()
        if not isinstance(record.size, (float, int)) or math.isnan(record.size) or not math.isfinite(record.size) or record.size < 0:
            record.size = 0.0
        # Handle None for source
        if record.source is None:
            raise ValueError("Source is empty: {}".format(record))
        record.source = record.source.lower()


        # Symbol checks
        if not record.symbol:
            raise ValueError("Symbol is empty: {}".format(record))
        if " " in record.symbol:
            raise ValueError("Symbol contains spaces: {}".format(record.symbol))

        # Timestamp checks
        if record.ts is None:
            raise ValueError("Timestamp is None: {}".format(record))
        if not isinstance(record.ts, datetime):
            raise ValueError("Timestamp is not a datetime: {}".format(record.ts))
        if record.ts.tzinfo is None or record.ts.tzinfo.utcoffset(record.ts) is None:
            raise ValueError("Timestamp is not timezone-aware: {}".format(record.ts))
        if record.ts - datetime.now(timezone.utc) > tolerance:
            raise ValueError("Timestamp is too far in the future: {}".format(record.ts))

        # Price checks
        if not isinstance(record.price, (float, int)):
            raise ValueError("Price is not a number: {}".format(record.price))
        if math.isnan(record.price) or not math.isfinite(record.price):
            raise ValueError("Price is NaN or infinite: {}".format(record.price))
        if record.price <= 0:
            raise ValueError("Price is not positive: {}".format(record.price))

        # Size checks
        if not isinstance(record.size, (float, int)):
            raise ValueError("Size is not a number: {}".format(record.size))
        if math.isnan(record.size) or not math.isfinite(record.size):
            raise ValueError("Size is NaN or infinite: {}".format(record.size))
        if record.size < 0:
            raise ValueError("Size is negative: {}".format(record.size))

        # Source check
        if not record.source:
            raise ValueError("Source is empty: {}".format(record))

        # Deduplicate: keep first occurrence only
        to_add: Tuple[str, datetime] = (record.symbol, record.ts)
        if to_add in seen_records:
            continue
        seen_records.add(to_add)
        val_records.append(record)
    return val_records