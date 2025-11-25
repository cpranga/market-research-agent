"""
Entry point for the full Market Research Agent pipeline.
Loads config, starts coordinator, and keeps the process alive.
"""
import asyncio
import sys
from ops.coordinator import main

def run():
    try:
        asyncio.run(main())
    except Exception as e:
        print("Pipeline failed: {}".format(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run()
