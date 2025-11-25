"""
Pipeline Coordinator for Market Research Agent
Schedules ingestion, analytics, and reasoning jobs; manages heartbeats, retries, and window locks.
"""
import asyncio
from core.scheduler import Scheduler
from ingest.fetcher import fetch_trades
from ingest.validator import validate_trades
from ingest.writer import write_trades
from analytics.orchestrator import run_pipeline
from reasoning.summarizer import summarize
from reasoning.gateway import generate_summary
from core.logging import info, error
from datetime import datetime, timezone, timedelta
from core.config import Config
from reasoning.summarizer import run_once

async def run_ingestion():
    try:
        info("[Ingestion] Starting fetch...")
        trades = await fetch_trades()
        info("[Ingestion] Fetched {} trades.".format(len(trades)))
        valid_trades = validate_trades(trades)
        info("[Ingestion] Validated {} trades.".format(len(valid_trades)))
        written = await write_trades(valid_trades)
        info("[Ingestion] Wrote {} trades to DB.".format(written))
        # Heartbeat: record ingestion timestamp (example, implement as needed)
        with open("ingestion_heartbeat.txt", "w") as hb:
            hb.write("Last ingestion: {}\n".format(datetime.now(timezone.utc).isoformat()))
    except Exception as e:
        error("[Ingestion] Error: {}".format(e))

async def run_analytics():
    # Run analytics pipeline for all symbols and windows
    # TODO: Auto-detect unprocessed windows
    # Placeholder: run once for all symbols
    symbols = Config.SYMBOLS
    start = datetime.utcnow() - timedelta(hours=6)
    end = datetime.utcnow()
    window_size = timedelta(minutes=1)
    await run_pipeline(symbols, start, end, window_size)

async def run_reasoning():
    # Generate summaries from latest metrics/events
    await run_once()

async def main():
    scheduler = Scheduler()
    scheduler.schedule(run_ingestion, interval=60)      # every 60s
    scheduler.schedule(run_analytics, interval=300)     # every 5min
    scheduler.schedule(run_reasoning, interval=600)     # every 10min
    # Summarizer scheduled every 10min (can adjust interval)
    from reasoning.summarizer import run_once
    scheduler.schedule(run_once, interval=600)
    await scheduler.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
