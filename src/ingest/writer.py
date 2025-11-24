from typing import List

from ingest.providers.base import TradeRecord
from ingest.writer_errors import WriterError
from core.db import execute

async def write(records: List[TradeRecord]) -> int:
    """
    Write TradeRecord objects to the database, enforcing idempotency via upsert.
    """
    if not records:
        return 0

    cnt_written = 0
    try:
        for record in records:
            try:
                await execute(
                    """
                    INSERT INTO raw_trades (symbol, ts, price, size, source)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (symbol, ts)
                    DO UPDATE SET price = EXCLUDED.price, size = EXCLUDED.size, source = EXCLUDED.source
                    """,
                    (record.symbol, record.ts, record.price, record.size, record.source)
                )
                cnt_written += 1
            except Exception as e:
                raise WriterError(f"Database error during write: {e}") from e
        return cnt_written
    except Exception as e:
        raise WriterError(f"Unexpected error during write: {e}") from e
