"""
Metrics computation for TradeWindow objects.
Each function is pure and testable, returning None for missing or insufficient data.
"""
from typing import Optional, Dict
import math
from analytics.aggregator import TradeWindow

def vwap(window: TradeWindow) -> Optional[float]:
	if not window.trades or window.total_volume == 0:
		return None
	total = sum(t.price * t.size for t in window.trades)
	return total / window.total_volume

def volatility(window: TradeWindow) -> Optional[float]:
	prices = [t.price for t in window.trades]
	if len(prices) < 2:
		return None
	mean = sum(prices) / len(prices)
	variance = sum((p - mean) ** 2 for p in prices) / (len(prices) - 1)
	return math.sqrt(variance)

def momentum(window: TradeWindow, prev_window: Optional[TradeWindow]) -> Optional[float]:
	if not prev_window or window.open_price is None or prev_window.close_price is None:
		return None
	return window.open_price - prev_window.close_price

def liquidity_ratio(window: TradeWindow) -> Optional[float]:
	if window.total_volume == 0 or window.num_trades == 0:
		return None
	return window.total_volume / window.num_trades

async def compute_metrics(window: TradeWindow, prev_window: Optional[TradeWindow] = None) -> Dict[str, Optional[float]]:
	"""
	Compute all metrics for a given window.
	Returns a dict of metric_name: value.
	"""
	return {
		"vwap": vwap(window),
		"volatility": volatility(window),
		"momentum": momentum(window, prev_window),
		"liquidity_ratio": liquidity_ratio(window),
	}