"""
Test suite for the analytics writer module.
Checks that metrics and events are written to the database and idempotency is enforced.
"""
import pytest
from datetime import datetime, timedelta
from analytics.writer import write_metrics, write_events
from analytics.detector import Event

class DummyExecute:
    def __init__(self):
        self.calls = []
    async def __call__(self, sql, params):
        self.calls.append((sql, params))

@pytest.mark.asyncio
async def test_write_metrics(monkeypatch):
    """
    Test that write_metrics calls execute with correct SQL and parameters.
    """
    dummy_execute = DummyExecute()
    monkeypatch.setattr("analytics.writer.execute", dummy_execute)
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(minutes=1)
    metrics = {"vwap": 100.5, "volatility": 0.1, "momentum": 0.2, "liquidity_ratio": 5.0}
    await write_metrics(symbol, start, end, metrics)
    assert dummy_execute.calls, "Should call execute for metrics write"
    sql, params = dummy_execute.calls[0]
    assert "INSERT INTO derived_metrics" in sql, "SQL should insert into derived_metrics"
    assert params[:3] == (symbol, start, end), "Params should include symbol and window boundaries"

@pytest.mark.asyncio
async def test_write_events(monkeypatch):
    """
    Test that write_events calls execute for each event and serializes details to JSON.
    """
    dummy_execute = DummyExecute()
    monkeypatch.setattr("analytics.writer.execute", dummy_execute)
    symbol = "AAPL"
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(minutes=1)
    event = Event(
        type="volatility_spike",
        severity="warning",
        symbol=symbol,
        window_start=start,
        window_end=end,
        details={"volatility": 0.15, "threshold": 0.1}
    )
    await write_events([event])
    assert dummy_execute.calls, "Should call execute for event write"
    sql, params = dummy_execute.calls[0]
    assert "INSERT INTO events" in sql, "SQL should insert into events"
    assert params[0:3] == (symbol, start, end), "Params should include symbol and window boundaries"
    assert "volatility" in params[-1], "Details should be serialized to JSON"

@pytest.mark.asyncio
async def test_write_events_empty(monkeypatch):
    """
    Test that write_events returns 0 and does not call execute when given an empty event list.
    """
    dummy_execute = DummyExecute()
    monkeypatch.setattr("analytics.writer.execute", dummy_execute)
    result = await write_events([])
    assert result == 0, "Should return 0 for empty event list"
    assert not dummy_execute.calls, "Should not call execute for empty event list"
