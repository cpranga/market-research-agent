from typing import List

from ingest.providers.base import TradeRecord
from ingest.writer_errors import WriterError
from core.db import execute

async def write(records: List[TradeRecord]) -> int:
    if not records:
        return 0

    cnt_written = 0
    try:
        for record in records:
            try:
                await execute(
                    "INSERT INTO raw_trades (symbol, ts, price, size, source) VALUES ($1, $2, $3, $4, $5)",
                    (record.symbol, record.ts, record.price, record.size, record.source)
                )
                cnt_written += 1
            except Exception as e:
                raise WriterError("Database error during write: {}".format(e)) from e
        return cnt_written
    except Exception as e:
        raise WriterError("Unexpected error during write: {}".format(e)) from e
