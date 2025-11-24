"""
Test suite for the analytics aggregator windowing logic.
This file checks that trades are correctly bucketed into windows and that summary statistics are accurate.
"""
import pytest
from datetime import datetime, timedelta
from analytics.aggregator import TradeWindow, build_windows
from ingest.providers.base import TradeRecord

def make_trade(symbol, ts, price, size, source="test"):
    """
    Helper for creating TradeRecords
    """
    return TradeRecord(symbol=symbol, ts=ts, price=price, size=size, source=source)

def test_build_windows_basic():
    """
    Verify basic window bucketing
    """
    # Let's create 3 trades, all in the same minute
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    window_size = timedelta(minutes=1)
    trades = [
        make_trade(symbol, start + timedelta(seconds=5), 100.0, 10.0),
        make_trade(symbol, start + timedelta(seconds=15), 101.0, 5.0),
        make_trade(symbol, start + timedelta(seconds=45), 99.5, 8.0),
    ]
    windows = build_windows(trades, start, start + window_size, window_size)
    assert len(windows) == 1, "Should create one window for one minute"
    win = windows[0]
    assert win.open_price == 100.0, "Open price should be the first trade's price"
    assert win.close_price == 99.5, "Close price should be the last trade's price"
    assert win.high_price == 101.0, "High price should be the max price"
    assert win.low_price == 99.5, "Low price should be the min price"
    assert win.total_volume == 23.0, "Total volume should sum all sizes"
    assert win.num_trades == 3, "Should count all trades"
    assert not win.missing_data, "Window should not be marked as missing data"

def test_build_windows_empty():
    """
    Verify building an empty window
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    window_size = timedelta(minutes=1)
    trades = []
    windows = build_windows(trades, start, start + window_size, window_size)
    assert len(windows) == 1, "Should still create one window even if no trades"
    win = windows[0]
    assert win.open_price is None, "Open price should be None for empty window"
    assert win.missing_data, "Window should be marked as missing data"

def test_build_windows_multiple():
    """
    Verify trades can be split across multiple windows
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    window_size = timedelta(minutes=1)
    trades = [
        make_trade(symbol, start + timedelta(seconds=5), 100.0, 10.0),
        make_trade(symbol, start + timedelta(seconds=65), 101.0, 5.0),
        make_trade(symbol, start + timedelta(seconds=125), 99.5, 8.0),
    ]
    windows = build_windows(trades, start, start + timedelta(minutes=3), window_size)
    assert len(windows) == 3, "Should create three windows for three minutes"
    assert windows[0].num_trades == 1, "First window should have one trade"
    assert windows[1].num_trades == 1, "Second window should have one trade"
    assert windows[2].num_trades == 1, "Third window should have one trade"

def test_build_windows_out_of_range():
    """
    Verify trades outside window are ignored
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    window_size = timedelta(minutes=1)
    trades = [
        make_trade(symbol, start - timedelta(seconds=10), 100.0, 10.0),  # before window
        make_trade(symbol, start + timedelta(minutes=1, seconds=1), 101.0, 5.0),  # after window
    ]
    windows = build_windows(trades, start, start + window_size, window_size)
    assert len(windows) == 1, "Should create one window"
    assert windows[0].num_trades == 0, "No trades should be assigned to window"
    assert windows[0].missing_data, "Window should be marked as missing data"
