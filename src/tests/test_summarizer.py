"""
Test for Summarizer Stage 3
Verifies summarizer inserts summary row and correct metadata.
"""
import asyncio
import pytest
from datetime import datetime
from core.db import init_pool, execute, fetch_one, close_pool
from reasoning.summarizer import run_once

@pytest.mark.asyncio
async def test_summarizer_inserts_summary():
    await init_pool()
    window_start = datetime(2025, 1, 1, 10, 0, 0)
    window_end = datetime(2025, 1, 1, 10, 1, 0)
    # Insert sample derived_metrics row
    await execute(
        """
        INSERT INTO derived_metrics (symbol, window_start, window_end, vwap, volatility, momentum, liquidity_ratio)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, window_start, window_end) DO NOTHING
        """,
        ("TEST", window_start, window_end, 100.0, 3.0, 1.0, 0.5)
    )
    # Insert sample event row
    await execute(
        """
        INSERT INTO events (symbol, window_start, window_end, type, severity)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (symbol, window_start, window_end, type) DO NOTHING
        """,
        ("TEST", window_start, window_end, "spike", "high")
    )
    await run_once()
    # Check summary row
    summary = await fetch_one(
        "SELECT * FROM summaries WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        ("TEST", window_start, window_end)
    )
    assert summary is not None
    assert summary["text"]
    assert summary["model"] == "rules"
    assert summary["prompt_version"] == "rules_v1"
    assert summary["tokens_used"] == 0
    await close_pool()
