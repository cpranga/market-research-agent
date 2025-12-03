import asyncio
from datetime import datetime, timezone
from typing import Callable, Awaitable, List, Optional, Tuple

from core.config import Config
from core.logging import info, error, debug
from ingest.fetcher import fetch_all
from ingest.validator import validate
from ingest.writer import write
from core.db import init_pool, close_pool


class Scheduler:
    """
    Minimal async scheduler for periodic jobs.
    """
    def __init__(self):
        self._jobs: List[Tuple[Callable[[], Awaitable], int]] = []

    def schedule(self, coro_func: Callable[[], Awaitable], interval: int):
        self._jobs.append((coro_func, interval))

    async def run_forever(self):
        while True:
            cycle_start = datetime.now(timezone.utc)
            for job, interval in self._jobs:
                try:
                    await job()
                except Exception as exc:
                    error("Scheduled job failed: {}".format(exc))
            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            # Use the minimum interval across jobs to pace the loop
            min_interval = min(interval for _, interval in self._jobs) if self._jobs else Config.SCHEDULER_INTERVAL_SEC
            sleep_for = max(0, min_interval - elapsed)
            if sleep_for:
                await asyncio.sleep(sleep_for)


async def run_once():
    debug("Starting single ingest cycle.")
    await init_pool()
    try:
        records = fetch_all()
        debug("Fetched {} raw records.".format(len(records)))

        validated = validate(records)
        debug("Validated {} records.".format(len(validated)))

        written = await write(validated)
        info("Single ingestion cycle complete: {} records written".format(written))
        return written
    finally:
        await close_pool()


async def run_scheduler():
    info("Schedule started with interval {} seconds.".format(Config.SCHEDULER_INTERVAL_SEC))
    await init_pool()
    try:
        while True:
            cycle_start = datetime.now(timezone.utc)
            try:
                debug("Starting new ingest cycle.")
                records = fetch_all()
                debug("Fetched {} raw records".format(len(records)))

                validated = validate(records)
                debug("Validated {} records.".format(len(validated)))

                written = await write(validated)
                info("Ingest cycle completed: {} records written.".format(written))
            except Exception as e:
                error("Ingest cycle failed: {}".format(e))

            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            delay = Config.SCHEDULER_INTERVAL_SEC - elapsed
            if delay > 0:
                debug("Sleeping {} seconds".format(delay))
                await asyncio.sleep(delay)
            else:
                debug("Cycle exceeded interval; restarting immediately.")
    except KeyboardInterrupt:
        info("Scheduler stopped manually.")
    except SystemExit:
        info("Scheduler shutting down.")
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
