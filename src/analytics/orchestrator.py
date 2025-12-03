"""
Analytics Pipeline Orchestrator
Coordinates the end-to-end flow: load trades, build windows, compute metrics, detect events, and write results to the database for each symbol and time range.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from core.db import init_pool
from analytics.aggregator import load_trades, build_windows
from analytics.metrics import compute_metrics
from core.utils import get_window_bounds
from analytics.detector import detect_events
from analytics.writer import write_metrics, write_events
from core.db import fetch_one
from core.logging import debug, info
from core.config import Config


async def run_pipeline(symbols: List[str], window_seconds: int) -> int:
    """
    Run the analytics pipeline for each symbol and all unprocessed time windows.
    Loads trades, builds windows, computes metrics, detects events, and writes results to the database.
    """
    await init_pool()
    sem = asyncio.Semaphore(Config.ANALYTICS_CONCURRENCY)
    processed_windows = 0

    async def process_symbol(symbol: str):
        async with sem:
            latest = await fetch_one(
                "SELECT MAX(window_end) as last_end FROM derived_metrics WHERE symbol = $1", (symbol,)
            )
            start = None
            if latest and latest.get("last_end"):
                start = latest["last_end"]
            else:
                first_trade = await fetch_one(
                    "SELECT MIN(ts) as first_ts FROM raw_trades WHERE symbol = $1", (symbol,)
                )
                start = first_trade["first_ts"] if first_trade and first_trade.get("first_ts") else None
            if not start:
                debug("No trades available for {}; skipping analytics.".format(symbol))
                return

            end = datetime.now(timezone.utc)
            trades = await load_trades(symbol, start, end)
            window_start, _ = get_window_bounds(start, window_seconds)
            if latest and start == latest.get("last_end"):
                window_start = start

            windows = build_windows(trades, window_start, end, timedelta(seconds=window_seconds))
            prev_window, prev_metrics = None, None
            for window in windows:
                metrics = compute_metrics(window, prev_window)
                events = detect_events(window, metrics, prev_window, prev_metrics)
                await write_metrics(symbol, window.window_start, window.window_end, metrics)
                await write_events(events)
                prev_window, prev_metrics = window, metrics
            if Config.ANALYTICS_DEBUG_SYMBOLS:
                info("[Analytics] Processed {} windows for {} at {}s.".format(len(windows), symbol, window_seconds))
            return len(windows)

    results = await asyncio.gather(*(process_symbol(sym) for sym in symbols))
    processed_windows = sum(r or 0 for r in results)
    return processed_windows
