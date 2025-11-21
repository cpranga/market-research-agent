from core.config import Config
from ingest.fetcher import fetch_all
from ingest.validator import validate
from ingest.writer import write
from core.logging import info, error, debug
from datetime import datetime, timezone
import time


import asyncio

async def run_once():
    debug("Starting single ingest cycle.")

    records = fetch_all()
    debug("Fetched {} raw records.".format(len(records)))

    validated = validate(records)
    debug("Validated {} records.".format(len(validated)))

    written = await write(validated)
    info("Single ingestion cycle complete: {} records written".format(written))

    return written


async def run_scheduler():
    info("Schedule started with interval {} seconds.".format(
        Config.SCHEDULER_INTERVAL_SEC
    ))

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
            
            # Maintain fixed interval
            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            delay = Config.SCHEDULER_INTERVAL_SEC - elapsed

            if delay > 0:
                debug("Sleeping {} seconds".format(delay))
                time.sleep(delay)
            else:
                debug("Cycle exceeded interval; restarting immedietly.")
    except KeyboardInterrupt:
        info("Scheduler stopped manually.")
    except SystemExit:
        info("Scheduler shutting down.")

if __name__ == "__main__":
    asyncio.run(run_scheduler())