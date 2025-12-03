"""
Reasoning module tests for Stage 3
"""
import pytest
import asyncio
from datetime import datetime
from core.db import init_pool, execute, fetch_one, close_pool
from reasoning.summarizer import run_once
from reasoning.rules import generate_text
from reasoning.prompt_templates import build_prompt

import pytest

@pytest.mark.asyncio
async def test_load_metrics_and_events():
    await init_pool()
    window_start = datetime(2025, 1, 1, 10, 0, 0)
    window_end = datetime(2025, 1, 1, 10, 1, 0)
    await execute(
        """
        INSERT INTO derived_metrics (symbol, window_start, window_end, vwap, volatility, momentum, liquidity_ratio)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, window_start, window_end) DO NOTHING
        """,
        ("TEST2", window_start, window_end, 100.0, 2.5, 0.5, 0.7)
    )
    await execute(
        """
        INSERT INTO events (symbol, window_start, window_end, type, severity)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (symbol, window_start, window_end, type) DO NOTHING
        """,
        ("TEST2", window_start, window_end, "volatility", "high")
    )
    await run_once()
    summary = await fetch_one(
        "SELECT * FROM summaries WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        ("TEST2", window_start, window_end)
    )
    assert summary is not None
    assert summary["text"]
    await close_pool()

@pytest.mark.asyncio
async def test_rule_system():
    bundle = {
        "metrics": {"volatility": 3.0, "momentum": 1.0},
        "events": [{"type": "volatility", "severity": "high"}],
        "window_start": datetime(2025, 1, 1, 10, 0, 0),
        "window_end": datetime(2025, 1, 1, 10, 1, 0),
        "symbol": "TEST3",
        "news": [],
        "sector": None,
        "market": None
    }
    text = generate_text(bundle)
    assert "Volatility event detected" in text

@pytest.mark.asyncio
async def test_prompt_template():
    bundle = {
        "metrics": {"volatility": 1.5, "momentum": -0.5},
        "events": [],
        "window_start": datetime(2025, 1, 1, 10, 0, 0),
        "window_end": datetime(2025, 1, 1, 10, 1, 0),
        "symbol": "TEST4",
        "news": [],
        "sector": None,
        "market": None
    }
    prompt = build_prompt(bundle)
    assert "Volatility was moderate." in prompt
    assert "Momentum trended downward." in prompt

@pytest.mark.asyncio
async def test_backfill_multiple_windows():
    from core.db import close_pool
    await init_pool()
    for i in range(3):
        window_start = datetime(2025, 1, 1, 10, i, 0)
        window_end = datetime(2025, 1, 1, 10, i+1, 0)
        await execute(
            """
            INSERT INTO derived_metrics (symbol, window_start, window_end, vwap, volatility, momentum, liquidity_ratio)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (symbol, window_start, window_end) DO NOTHING
            """,
            ("TEST5", window_start, window_end, 100.0, 2.0, 0.5, 0.7)
        )
    await run_once(batch_size=3)
    for i in range(3):
        window_start = datetime(2025, 1, 1, 10, i, 0)
        window_end = datetime(2025, 1, 1, 10, i+1, 0)
        summary = await fetch_one(
            "SELECT * FROM summaries WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
            ("TEST5", window_start, window_end)
        )
        assert summary is not None
    await close_pool()

