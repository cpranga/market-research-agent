"""
Context Loader Stub for Summarizer
Provides empty context for news, sector, and market. Extend in Stage 4.
"""

from core.db import fetch

async def load_news(symbol, window_start, window_end):
    rows = await fetch(
        "SELECT * FROM context_news WHERE symbol = $1 AND published_at >= $2 AND published_at < $3",
        (symbol, window_start, window_end)
    )
    return [dict(row) for row in rows]

async def load_sector(symbol, window_start, window_end):
    rows = await fetch(
        "SELECT * FROM context_sector WHERE window_start = $1 AND window_end = $2",
        (window_start, window_end)
    )
    return rows[0] if rows else None

async def load_market(window_start, window_end):
    rows = await fetch(
        "SELECT * FROM context_market WHERE window_start = $1 AND window_end = $2",
        (window_start, window_end)
    )
    return rows[0] if rows else None


async def load_company(symbol):
    rows = await fetch(
        "SELECT * FROM context_company WHERE symbol = $1",
        (symbol,)
    )
    return rows[0] if rows else None


async def load_financials(symbol):
    rows = await fetch(
        "SELECT * FROM context_financials WHERE symbol = $1 ORDER BY as_of DESC LIMIT 1",
        (symbol,)
    )
    return rows[0] if rows else None


async def load_strategies(symbol):
    rows = await fetch(
        """
        SELECT * FROM strategies
        WHERE active = TRUE AND (symbols IS NULL OR array_length(symbols,1) IS NULL OR $1 = ANY(symbols))
        """,
        (symbol,)
    )
    return rows
