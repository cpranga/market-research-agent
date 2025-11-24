"""
This module loads raw data from Postgres, and groups it into analytical windows,
creating structured data ready for analysis. It does not analyze the data itself;
 it prepare and shapes data to later be analyzed.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Union, Dict, Optional
from ingest.providers.base import TradeRecord
from math import ceil
from core.db import fetch

class TradeWindow:
    def __init__(self, trades: List[TradeRecord], window_start: datetime, window_end: datetime) -> None:
        if trades and len({record.symbol for record in trades}) != 1:
            raise ValueError("All trades in a TradeWindow must have the same symbol.")
        self.symbol: Optional[str] = trades[0].symbol if trades else None
        self.window_start: datetime = window_start
        self.window_end: datetime = window_end
        self.trades: List[TradeRecord] = trades

        if trades:
            # Ensure trades are sorted by timestamp
            sorted_trades = sorted(trades, key=lambda t: t.ts)
            self.open_price: float = sorted_trades[0].price
            self.close_price: float = sorted_trades[-1].price
            self.high_price: float = max(t.price for t in sorted_trades)
            self.low_price: float = min(t.price for t in sorted_trades)
            self.total_volume: float = sum(t.size for t in sorted_trades)
            self.num_trades: int = len(sorted_trades)
            self.missing_data: bool = False
        else:
            self.open_price = None
            self.close_price = None
            self.high_price = None
            self.low_price = None
            self.total_volume = 0.0
            self.num_trades = 0
            self.missing_data = True

def build_windows(
        trades: List[TradeRecord],
        window_start: datetime,
        window_end: datetime,
        window_size: timedelta
) -> List[TradeWindow]:
    # Create enough windows to handle the entire duration
    buckets: List[List[TradeRecord]] = []
    windows: List[TradeWindow] = []
    duration = (window_end - window_start).total_seconds()
    window_seconds = window_size.total_seconds()
    num_windows = ceil(duration / window_seconds)
    for _ in range(num_windows):
        buckets.append([])
    
    # Populate the trade buckets with fitting trade records
    for trade in trades:
        if trade.ts < window_start or trade.ts >= window_end: continue
        offset = (trade.ts - window_start).total_seconds()
        bucket_idx = int(offset // window_seconds)
        buckets[bucket_idx].append(trade)
    
    win_start = window_start
    for bucket in buckets:
        windows.append(TradeWindow(bucket, win_start, win_start + window_size))
        win_start += window_size
    
    return windows

async def load_trades(
        symbol: str,
        start: datetime,
        end: datetime
) -> List[TradeRecord]:
    res = await fetch(
        "SELECT * from raw_trades where symbol = $1 and ts >= $2 and ts < $3",
        (symbol, start, end))
    records: List[TradeRecord] = [TradeRecord(**raw_trade) for raw_trade in res]
    records.sort(key=lambda r:r.ts)
    return records

async def aggregate (
        symbol: str,
        start: datetime,
        end:datetime,
        window_size: timedelta
) -> List[TradeWindow]:
    trades = await load_trades(symbol, start, end)
    windows = build_windows(trades, start, end, window_size)
    return windows