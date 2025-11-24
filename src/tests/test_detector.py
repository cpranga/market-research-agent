"""
Test suite for the analytics event detector module.
Checks that detect_events returns correct Event objects for various scenarios.
"""
import pytest
from datetime import datetime, timedelta
from analytics.aggregator import TradeWindow
from analytics.detector import Event, detect_events
from ingest.providers.base import TradeRecord

class DummyConfig:
    VOLATILITY_SPIKE_THRESHOLD = 0.1
    ABNORMAL_PRICE_CHANGE_THRESHOLD = 2.0

# Patch Config for testing
import analytics.detector
analytics.detector.Config = DummyConfig

def make_trade(symbol, ts, price, size, source="test"):
    return TradeRecord(symbol=symbol, ts=ts, price=price, size=size, source=source)

def make_window(trades, start, size):
    return TradeWindow(trades, start, start + size)

def test_volatility_spike():
    """
    Test that a volatility spike event is detected when volatility exceeds the threshold.
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0), make_trade(symbol, start + timedelta(seconds=10), 110.0, 5.0)]
    window = make_window(trades, start, timedelta(minutes=1))
    metrics = {"volatility": 0.15, "momentum": 0.0}
    events = detect_events(window, metrics)
    assert any(e.type == "volatility_spike" for e in events), "Should detect volatility spike event"

def test_momentum_reversal():
    """
    Test that a momentum reversal event is detected when momentum changes sign compared to previous window.
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0)]
    window = make_window(trades, start, timedelta(minutes=1))
    metrics = {"volatility": 0.0, "momentum": 1.0}
    prev_metrics = {"volatility": 0.0, "momentum": -1.0}
    events = detect_events(window, metrics, None, prev_metrics)
    assert any(e.type == "momentum_reversal" for e in events), "Should detect momentum reversal event"

def test_abnormal_price_change():
    """
    Test that an abnormal price change event is detected when the price change exceeds the threshold.
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0), make_trade(symbol, start + timedelta(seconds=10), 103.0, 5.0)]
    window = make_window(trades, start, timedelta(minutes=1))
    metrics = {"volatility": 0.0, "momentum": 0.0}
    events = detect_events(window, metrics)
    assert any(e.type == "abnormal_price_change" for e in events), "Should detect abnormal price change event"

def test_no_event():
    """
    Test that no events are detected when all metrics are within normal thresholds.
    """
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    trades = [make_trade(symbol, start, 100.0, 10.0), make_trade(symbol, start + timedelta(seconds=10), 100.5, 5.0)]
    window = make_window(trades, start, timedelta(minutes=1))
    metrics = {"volatility": 0.05, "momentum": 0.5}
    events = detect_events(window, metrics)
    assert len(events) == 0, "Should not detect any events"
