from typing import List
from datetime import datetime
import json

from analytics.detector import Event
from ingest.writer_errors import WriterError
from core.db import execute

async def write_metrics(
        symbol: str,
        window_start: datetime,
        window_end: datetime,
        metrics: dict
) -> None:
    """
    Write derived metrics to the database, enforcing idempotency via upsert.
    """
    try:
        try:
            await execute(
                """
                INSERT INTO derived_metrics (symbol, window_start, window_end, vwap, volatility, momentum, liquidity_ratio)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (symbol, window_start, window_end)
                DO UPDATE SET vwap = EXCLUDED.vwap, volatility = EXCLUDED.volatility, momentum = EXCLUDED.momentum, liquidity_ratio = EXCLUDED.liquidity_ratio
                """,
                (symbol, window_start, window_end, metrics["vwap"], metrics["volatility"], metrics["momentum"], metrics["liquidity_ratio"])
            )
        except Exception as e:
            raise WriterError("Database error during write: {}".format(e))
    except Exception as e:
        raise WriterError("Unexpected error during write: {}".format(e))

async def write_events(
        events: List[Event]
) -> int:
    """
    Write event objects to the database, enforcing idempotency via upsert and serializing details to JSON.
    """
    if not events:
        return 0
    cnt_written = 0
    try:
        for event in events:
            try:
                await execute(
                    """
                    INSERT INTO events (symbol, window_start, window_end, type, severity, details)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (symbol, window_start, window_end, type)
                    DO UPDATE SET severity = EXCLUDED.severity, details = EXCLUDED.details
                    """,
                    (
                        event.symbol,
                        event.window_start,
                        event.window_end,
                        event.type,
                        event.severity,
                        json.dumps(event.details, default=float),
                    )
                )
                cnt_written += 1
            except Exception as e:
                raise WriterError("Database error during write: {}".format(e))
    except Exception as e:
        raise WriterError("Unexpected error during write: {}".format(e))
    return cnt_written
