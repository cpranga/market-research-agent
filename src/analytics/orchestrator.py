"""
Analytics Pipeline Orchestrator
Coordinates the end-to-end flow: load trades, build windows, compute metrics, detect events, and write results to the database for each symbol and time range.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from core.db import init_pool, close_pool
from analytics.aggregator import load_trades, build_windows
from analytics.metrics import compute_metrics
from analytics.detector import detect_events
from analytics.writer import write_metrics, write_events

async def run_pipeline(symbols: List[str], start: datetime, end: datetime, window_size: timedelta):
	"""
	Run the analytics pipeline for each symbol and time range.
	Loads trades, builds windows, computes metrics, detects events, and writes results to the database.
	"""
	await init_pool()
	try:
		for symbol in symbols:
			trades = await load_trades(symbol, start, end)
			windows = build_windows(trades, start, end, window_size)
			prev_window, prev_metrics = None, None
			for window in windows:
				metrics = await compute_metrics(window, prev_window)
				events = detect_events(window, metrics, prev_window, prev_metrics)
				await write_metrics(symbol, window.window_start, window.window_end, metrics)
				await write_events(events)
				prev_window, prev_metrics = window, metrics
	finally:
		await close_pool()

if __name__ == "__main__":
	# Example usage: run for a list of symbols and a fixed time range
	symbols = ["AAPL", "GOOG", "MSFT"]
	start = datetime(2025, 1, 1, 10, 0, 0)
	end = datetime(2025, 1, 1, 16, 0, 0)
	window_size = timedelta(minutes=1)
	asyncio.run(run_pipeline(symbols, start, end, window_size))
