# Project Structure

market-agent/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Load env vars, DB config, API keys
│   │   ├── db.py                  # Postgres connection, schema migrations
│   │   ├── logging.py             # Unified logging setup with rich
│   │   ├── scheduler.py           # APScheduler or asyncio-based loop
│   │   └── utils.py               # Common helpers, hashing, time windows
│   │
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── fetcher.py             # Pull data from APIs / yfinance
│   │   ├── validator.py           # Timestamp & schema checks
│   │   └── writer.py              # Insert raw trades into Postgres
│   │
│   ├── context/
│   │   ├── __init__.py
│   │   ├── harvester.py           # Fetch external news/sector/market data
│   │   ├── cache.py               # TTL caching, deduplication by hash
│   │   └── normalizer.py          # Normalize headlines, indices, etc.
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── metrics.py             # VWAP, SMA/EMA, volatility, momentum
│   │   ├── aggregator.py          # Window aggregation and computation
│   │   └── detector.py            # Event/Anomaly detection logic
│   │
│   ├── reasoning/
│   │   ├── __init__.py
│   │   ├── gateway.py             # Abstract interface to LLM providers
│   │   ├── rules.py               # Rule-based summaries
│   │   ├── prompt_templates.py    # Structured prompt builders
│   │   └── summarizer.py          # Entry point for summary generation
│   │
│   ├── ops/
│   │   ├── __init__.py
│   │   ├── coordinator.py         # Drives stage scheduling, backfill, retries
│   │   ├── heartbeat.py           # Process heartbeat + lag metrics
│   │   ├── audit.py               # Track config/model changes
│   │   └── monitor.py             # Observability hooks, metrics export
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py              # Read-only FastAPI/Flask endpoints
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py
│   │   │   ├── summaries.py
│   │   │   └── status.py
│   │   └── schemas.py             # Pydantic models for API responses
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_ingest.py
│       ├── test_analytics.py
│       ├── test_reasoning.py
│       └── fixtures/
│           ├── raw_trades_sample.csv
│           └── context_news_sample.json
│
├── sql/
│   ├── schema.sql                 # Full DB schema
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   ├── 002_metrics.sql
│   │   └── 003_summaries.sql
│   └── seeds.sql                  # Optional bootstrap data
│
├── scripts/
│   ├── init_db.py                 # Initialize DB schema
│   ├── run_ingest.py              # Manual trigger for ingestion
│   ├── run_analytics.py           # Manual analytics run
│   ├── run_reasoning.py           # Manual summary generation
│   └── run_all.py                 # End-to-end local pipeline loop
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   ├── ops_runbook.md
│   ├── metrics_reference.md
│   └── prompt_examples.md
│
└── data/
    ├── cache/
    ├── logs/
    ├── exports/
    └── tmp/

# Summary
- Modular by function (ingest → analytics → reasoning → ops).
- PostgreSQL-driven persistence layer.
- Clear separation of logic, orchestration, and configuration.
- Ready for local development or containerized deployment.
