"""
Test suite for the analytics metrics module.
Checks that metric functions return correct values for various TradeWindow scenarios.
"""
import pytest
from datetime import datetime, timedelta
from analytics.aggregator import TradeWindow
from analytics.metrics import vwap, volatility, momentum, liquidity_ratio, compute_metrics
from ingest.providers.base import TradeRecord

def make_trade(symbol, ts, price, size, source="test"):
    return TradeRecord(symbol=symbol, ts=ts, price=price, size=size, source=source)

def make_window(trades, start, size):
    return TradeWindow(trades, start, start + size)

def test_vwap_basic():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [
        make_trade(symbol, start, 100.0, 10.0),
        make_trade(symbol, start + timedelta(seconds=10), 102.0, 5.0),
    ]
    window = make_window(trades, start, timedelta(minutes=1))
    expected_vwap = (100.0*10.0 + 102.0*5.0) / (10.0 + 5.0)
    assert vwap(window) == expected_vwap, "VWAP should be volume-weighted average price"

def test_vwap_empty():
    window = make_window([], datetime(2025, 1, 1, 10, 0, 0), timedelta(minutes=1))
    assert vwap(window) is None, "VWAP should be None for empty window"

def test_volatility_basic():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [
        make_trade(symbol, start, 100.0, 10.0),
        make_trade(symbol, start + timedelta(seconds=10), 102.0, 5.0),
        make_trade(symbol, start + timedelta(seconds=20), 98.0, 8.0),
    ]
    window = make_window(trades, start, timedelta(minutes=1))
    prices = [100.0, 102.0, 98.0]
    mean = sum(prices) / len(prices)
    variance = sum((p - mean) ** 2 for p in prices) / (len(prices) - 1)
    expected_vol = variance ** 0.5
    assert abs(volatility(window) - expected_vol) < 1e-8, "Volatility should be sample stddev of prices"

def test_volatility_single():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0)]
    window = make_window(trades, start, timedelta(minutes=1))
    assert volatility(window) is None, "Volatility should be None for single trade"

def test_momentum_basic():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades1 = [make_trade(symbol, start, 100.0, 10.0)]
    trades2 = [make_trade(symbol, start + timedelta(minutes=1), 105.0, 5.0)]
    win1 = make_window(trades1, start, timedelta(minutes=1))
    win2 = make_window(trades2, start + timedelta(minutes=1), timedelta(minutes=1))
    assert momentum(win2, win1) == 105.0 - 100.0, "Momentum should be open - previous close"

def test_momentum_missing_prev():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0)]
    win = make_window(trades, start, timedelta(minutes=1))
    assert momentum(win, None) is None, "Momentum should be None if previous window missing"

def test_liquidity_ratio_basic():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [
        make_trade(symbol, start, 100.0, 10.0),
        make_trade(symbol, start + timedelta(seconds=10), 102.0, 5.0),
    ]
    window = make_window(trades, start, timedelta(minutes=1))
    expected_ratio = (10.0 + 5.0) / 2
    assert liquidity_ratio(window) == expected_ratio, "Liquidity ratio should be total volume / num trades"

def test_liquidity_ratio_empty():
    window = make_window([], datetime(2025, 1, 1, 10, 0, 0), timedelta(minutes=1))
    assert liquidity_ratio(window) is None, "Liquidity ratio should be None for empty window"

@pytest.mark.asyncio
async def test_compute_metrics_bundle():
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades1 = [make_trade(symbol, start, 100.0, 10.0)]
    trades2 = [make_trade(symbol, start + timedelta(minutes=1), 105.0, 5.0)]
    win1 = make_window(trades1, start, timedelta(minutes=1))
    win2 = make_window(trades2, start + timedelta(minutes=1), timedelta(minutes=1))
    metrics = await compute_metrics(win2, win1)
    assert set(metrics.keys()) == {"vwap", "volatility", "momentum", "liquidity_ratio"}, "Should compute all metrics"
    assert metrics["momentum"] == 105.0 - 100.0, "Momentum should match expected value"
