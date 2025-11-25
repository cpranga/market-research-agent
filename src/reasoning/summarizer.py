"""
Stage-3 Summarizer Worker
Finds unsummarized windows, loads metrics/events, builds prompt, generates text, writes summary.
"""
import asyncio
from core.db import fetch_one, fetch, execute, init_pool
from core.config import Config
from reasoning.prompt_templates import build_prompt
from reasoning.gateway import summarize

async def find_next_window_to_summarize():
    # Find latest derived_metrics window not yet summarized
    row = await fetch_one(
        """
        SELECT symbol, window_start, window_end
        FROM derived_metrics
        WHERE (symbol, window_start, window_end) NOT IN (
            SELECT symbol, window_start, window_end FROM summaries
        )
        ORDER BY window_start ASC
        LIMIT 1
        """
    )
    return row

async def load_metrics_and_events(symbol, window_start, window_end):
    metrics = await fetch_one(
        "SELECT * FROM derived_metrics WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        (symbol, window_start, window_end)
    )
    events = await fetch(
        "SELECT * FROM events WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        (symbol, window_start, window_end)
    )
    return {"metrics": metrics, "events": events, "window_start": window_start, "window_end": window_end, "symbol": symbol}

async def write_summary(symbol, window_start, window_end, text, model, prompt_version):
    await execute(
        """
        INSERT INTO summaries (symbol, window_start, window_end, model, prompt_version, text, tokens_used)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, window_start, window_end) DO NOTHING
        """,
        (symbol, window_start, window_end, model, prompt_version, text, 0)
    )

async def run_once():
    window = await find_next_window_to_summarize()
    if not window:
        return
    bundle = await load_metrics_and_events(window["symbol"], window["window_start"], window["window_end"])
    prompt = build_prompt(bundle)
    text = summarize(bundle)
    await write_summary(
        symbol=window["symbol"],
        window_start=window["window_start"],
        window_end=window["window_end"],
        text=text,
        model="rules_v1",
        prompt_version="v1"
    )

async def main():
    await init_pool()
    await run_once()

if __name__ == "__main__":
    asyncio.run(main())
