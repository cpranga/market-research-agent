"""
Stage-3 Summarizer Worker
Finds unsummarized windows, loads metrics/events, builds prompt, generates text, writes summary.
"""
import asyncio
from core.db import fetch_one, fetch, execute, init_pool, close_pool
from core.config import Config
from reasoning.prompt_templates import build_prompt, build_action_prompt
from reasoning.gateway import summarize, generate_from_prompt
from reasoning import context_loader
from core.logging import info, error, debug
from reasoning.rules import generate_action
import json


async def generate_action_decision(bundle):
    """
    Use AI (local/cloud) to produce an action if configured; otherwise fall back to rules.
    """
    mode = (Config.SUMMARY_MODEL or "rules").lower()
    if mode == "rules":
        return generate_action(bundle)
    # Build action prompt and ask model
    prompt = build_action_prompt(bundle)
    try:
        raw = generate_from_prompt(prompt)
        action_obj = json.loads(raw)
        # Expect action + justification; enforce keys
        if not isinstance(action_obj, dict):
            raise ValueError("Action response not a dict")
        action = action_obj.get("action")
        justification = action_obj.get("justification")
        if action and justification:
            return action_obj
    except Exception as exc:
        error("AI action generation failed; falling back to rules. Error: {}".format(exc))
    return generate_action(bundle)

async def find_unsummarized_windows(batch_size=20):
    rows = await fetch(
        """
        SELECT dm.symbol, dm.window_start, dm.window_end
        FROM derived_metrics dm
        LEFT JOIN summaries s ON (
            s.symbol = dm.symbol
            AND s.window_start = dm.window_start
            AND s.window_end = dm.window_end
        )
        WHERE s.id IS NULL
        ORDER BY dm.window_start ASC
        LIMIT {0}
        """.format(batch_size)
    )
    return rows

async def load_metrics_and_events(symbol, window_start, window_end):
    metrics = await fetch_one(
        "SELECT * FROM derived_metrics WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        (symbol, window_start, window_end)
    )
    events = await fetch(
        "SELECT * FROM events WHERE symbol = $1 AND window_start = $2 AND window_end = $3",
        (symbol, window_start, window_end)
    )
    news = await context_loader.load_news(symbol, window_start, window_end)
    sector = await context_loader.load_sector(symbol, window_start, window_end)
    market = await context_loader.load_market(window_start, window_end)
    company = await context_loader.load_company(symbol)
    financials = await context_loader.load_financials(symbol)
    strategies = await context_loader.load_strategies(symbol)
    bundle = {
        "metrics": metrics,
        "events": events,
        "window_start": window_start,
        "window_end": window_end,
        "symbol": symbol,
        "news": news,
        "sector": sector,
        "market": market,
        "company": company,
        "financials": financials,
        "strategies": strategies,
    }
    return bundle

async def write_summary(symbol, window_start, window_end, text, model, prompt_version):
    await execute(
        """
        INSERT INTO summaries (symbol, window_start, window_end, model, prompt_version, text, tokens_used)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, window_start, window_end) DO NOTHING
        """,
        (symbol, window_start, window_end, model, prompt_version, text, 0)
    )

async def write_action(symbol, window_start, window_end, action, justification, source="rules"):
    await execute(
        """
        INSERT INTO actions (symbol, window_start, window_end, action, justification, source)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (symbol, window_start, window_end, action) DO UPDATE SET justification = EXCLUDED.justification, source = EXCLUDED.source
        """,
        (symbol, window_start, window_end, action, justification, source)
    )

async def run_once(batch_size=10):
    await init_pool()
    actions_written = 0
    summaries_written = 0
    try:
        windows = await find_unsummarized_windows(batch_size=batch_size)
        if not windows:
            return 0, 0
        for window in windows:
            bundle = await load_metrics_and_events(window["symbol"], window["window_start"], window["window_end"])
            prompt = build_prompt(bundle)
            text = summarize({"prompt": prompt, "bundle": bundle})
            model_version = "rules"
            prompt_version = "rules_v1"
            action_obj = await generate_action_decision(bundle)
            await write_summary(
                symbol=window["symbol"],
                window_start=window["window_start"],
                window_end=window["window_end"],
                text=text,
                model=model_version,
                prompt_version=prompt_version
            )
            summaries_written += 1
            await write_action(
                symbol=window["symbol"],
                window_start=window["window_start"],
                window_end=window["window_end"],
                action=action_obj.get("action"),
                justification=action_obj.get("justification"),
                source=model_version,
            )
            actions_written += 1
    finally:
        await close_pool()
    return summaries_written, actions_written

async def run_backfill(batch_size=20):
    await init_pool()
    actions_written = 0
    summaries_written = 0
    try:
        windows = await find_unsummarized_windows(batch_size=batch_size)
        for window in windows:
            bundle = await load_metrics_and_events(window["symbol"], window["window_start"], window["window_end"])
            prompt = build_prompt(bundle)
            text = summarize({"prompt": prompt, "bundle": bundle})
            action_obj = await generate_action_decision(bundle)
            await write_summary(
                symbol=window["symbol"],
                window_start=window["window_start"],
                window_end=window["window_end"],
                text=text,
                model="rules",
                prompt_version="rules_v1"
            )
            summaries_written += 1
            await write_action(
                symbol=window["symbol"],
                window_start=window["window_start"],
                window_end=window["window_end"],
                action=action_obj.get("action"),
                justification=action_obj.get("justification"),
                source="rules",
            )
            actions_written += 1
    finally:
        await close_pool()
    return summaries_written, actions_written

async def main():
    await init_pool()
    await run_once()

if __name__ == "__main__":
    asyncio.run(main())
