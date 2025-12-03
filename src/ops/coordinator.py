"""
Pipeline Coordinator for Market Research Agent
Schedules ingestion, analytics, and reasoning jobs; manages heartbeats, retries, and window locks.
"""

import asyncio
from core.scheduler import Scheduler
from ingest.fetcher import fetch_all
from ingest.validator import validate
from ingest.writer import write
from analytics.orchestrator import run_pipeline
from reasoning.summarizer import run_once, run_backfill
from core.logging import info, error
from datetime import datetime, timezone, timedelta
from core.config import Config
from core.db import log_audit, get_lag, init_pool, close_pool
from ops.heartbeat import heartbeat
from context.harvester import harvest_news, harvest_company_profiles, harvest_financials

async def run_ingestion():
    try:
        start_ts = datetime.now(timezone.utc)
        info("[Ingestion] Starting fetch...")
        trades = fetch_all()
        info("[Ingestion] Fetched {0} trades.".format(len(trades)))
        valid = validate(trades)
        info("[Ingestion] Validated {0} trades.".format(len(valid)))
        written = await write(valid)
        info("[Ingestion] Wrote {0} trades to DB.".format(written))
        elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
        info("[Ingestion] Cycle summary: fetched={0}, validated={1}, written={2}, elapsed={3:.2f}s".format(
            len(trades), len(valid), written, elapsed))
        await heartbeat("ingestion", lag_seconds=0.0, errors=0)
    except Exception as e:
        await heartbeat("ingestion", lag_seconds=0.0, errors=1)
        error("[Ingestion] Error: {0}".format(e))

async def run_analytics():
    # Run analytics pipeline for all symbols and windows
    symbols = Config.SYMBOLS
    for window_size_seconds in Config.ANALYTICS_WINDOWS_SECONDS:
        info("[Analytics] Starting analytics for symbols: {0} at window {1}s".format(symbols, window_size_seconds))
        try:
            start_ts = datetime.now(timezone.utc)
            processed = await run_pipeline(symbols, window_size_seconds)
            elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
            info("[Analytics] Completed analytics pass for window {0}s. windows={1}, elapsed={2:.2f}s".format(
                window_size_seconds, processed, elapsed))
            await heartbeat("analytics", lag_seconds=0.0, errors=0)
        except Exception as e:
            await heartbeat("analytics", lag_seconds=0.0, errors=1)
            error("[Analytics] Error (window {0}s): {1}".format(window_size_seconds, e))

async def run_summarizer():
    # Summarizer backfill: summarize up to 20 unsummarized windows
    try:
        info("[Summarizer] Starting summarizer backfill.")
        start_ts = datetime.now(timezone.utc)
        summaries_written, actions_written = await run_backfill(batch_size=20)
        elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
        info("[Summarizer] Completed summarizer backfill. summaries={0}, actions={1}, elapsed={2:.2f}s".format(
            summaries_written, actions_written, elapsed))
        await heartbeat("summarizer", lag_seconds=0.0, errors=0)
        info("[Summarizer] Completed summarizer backfill.")
    except Exception as e:
        await heartbeat("summarizer", lag_seconds=0.0, errors=1)
        error("[Summarizer] Error: {0}".format(e))

async def main():
    await init_pool()
    async def ingestion_loop():
        while True:
            try:
                await run_ingestion()
            except Exception as exc:
                error("[IngestionLoop] Error: {}".format(exc))
            await asyncio.sleep(Config.INGEST_INTERVAL_SEC)

    async def analytics_loop():
        while True:
            try:
                await run_analytics()
            except Exception as exc:
                error("[AnalyticsLoop] Error: {}".format(exc))
            await asyncio.sleep(Config.ANALYTICS_INTERVAL_SEC)

    async def context_loop():
        while True:
            try:
                info("[Context] Harvesting news.")
                count = await harvest_news()
                info("[Context] Harvested {} news items.".format(count))
                info("[Context] Harvesting company profiles.")
                await harvest_company_profiles()
                info("[Context] Harvesting financials.")
                await harvest_financials()
            except Exception as exc:
                error("[ContextLoop] Error: {}".format(exc))
            await asyncio.sleep(Config.CONTEXT_INTERVAL_SEC)

    async def summarizer_loop():
        while True:
            try:
                await run_summarizer()
            except Exception as exc:
                error("[SummarizerLoop] Error: {}".format(exc))
            await asyncio.sleep(Config.SUMMARIZER_INTERVAL_SEC)

    try:
        await asyncio.gather(
            ingestion_loop(),
            analytics_loop(),
            context_loop(),
            summarizer_loop(),
        )
    finally:
        await close_pool()

if __name__ == "__main__":
    asyncio.run(main())
