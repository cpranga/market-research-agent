Market Research Agent
=====================

An autonomous market-analysis loop that ingests live quotes, computes metrics and events, summarizes each window, and records operational heartbeats. Once started, it runs continuously and idempotently, filling `raw_trades`, `derived_metrics`, `events`, and `summaries`.

Contents
--------
- What it does
- Prerequisites
- Configuration
- Database setup
- Running the agent
- Monitoring and health
- Testing

What it does
------------
- Ingestion: pulls quotes for configured symbols, validates/dedupes, upserts into `raw_trades` (unique on `(symbol, ts)`).
- Analytics: resumes from the last processed window end, builds windows, computes VWAP/volatility/momentum/liquidity_ratio, detects events, upserts into `derived_metrics` and `events`.
- Reasoning: finds metric windows without summaries, loads metrics/events/context, generates deterministic rule-based analyses with a Buy/Hold/Sell recommendation, inserts into `summaries` once per window.
- Ops: writes heartbeats to `ops_heartbeats` after each stage to expose lag/health; audit helpers exist for future config/version changes.
- Coordinator: orchestrates ingestion → analytics → summarizer in sequence on a schedule, loops forever.

Prerequisites
-------------
- Python 3.11+ (async support).
- PostgreSQL reachable via `DATABASE_URL`.
- Finnhub API key (if using `finnhub` provider).

Configuration
-------------
Environment variables (see `core/config.py` for defaults):
- `DATABASE_URL` (required): Postgres DSN, e.g. `postgresql://user:pass@localhost:5432/db`.
- `SYMBOLS`: comma-separated symbols, e.g. `AAPL,MSFT`.
- `API_PROVIDER`: currently `finnhub` supported.
- `FINNHUB_API_KEY`: required when `API_PROVIDER=finnhub`.
- `ENABLE_NEWS_HARVEST`: fetch Finnhub news into `context_news` (default true).
- `NEWS_CATEGORY`: Finnhub news category (default `general`).
- `REQUEST_DELAY`: seconds to sleep between symbol fetches (default 0.2).
- `SCHEDULER_INTERVAL_SEC`: ingestion scheduler interval (default 20).
- `ANALYTICS_WINDOW_SECONDS`: comma-separated window sizes in seconds (default `60`), e.g. `60,300,900`.
- `ANALYTICS_CONCURRENCY`: max concurrent symbols processed in analytics (default 5).
- `LOG_LEVEL`, `DEBUG`, `ENABLE_LOG_COLORS`: logging controls.
- Strategies: add rows to `strategies` (name, description, rules text, symbols[], active) to include user-defined strategies in summaries.
- Summary model selection:
  - `SUMMARY_MODEL`: `rules` (default), `local`, or `cloud`.
  - `LOCAL_SUMMARY_ENDPOINT`: URL for local LLM HTTP endpoint (for `SUMMARY_MODEL=local`, TGI- or Ollama-compatible).
  - `LOCAL_SUMMARY_MODEL`: model name to send to the local endpoint (default `Qwen/Qwen2.5-14B-Instruct`).
  - `LOCAL_SUMMARY_BACKEND`: `tgi` (Hugging Face Text Generation Inference) or `ollama` (default `tgi`).
  - `CLOUD_SUMMARY_ENDPOINT`, `CLOUD_SUMMARY_API_KEY`, `CLOUD_SUMMARY_MODEL`: HTTP + bearer token settings for cloud LLM.
  - `SUMMARY_MAX_TOKENS`: cap for LLM responses (default 256).
- Actions: model can propose actions when `SUMMARY_MODEL` is `local` or `cloud`; otherwise rules-based actions are used. Actions are stored in `actions` with justification.

Database setup
--------------
1) Create your database and set `DATABASE_URL`.
2) Apply the schema:
   ```sh
   psql "$DATABASE_URL" -f sql/schema.sql
   ```
   This creates core tables and enforces a unique index on `(symbol, ts)` for `raw_trades`.

Install dependencies
--------------------
```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Running the agent
-----------------
Start the coordinator; it will loop forever:
```sh
python -m ops.coordinator
```
What happens each cycle:
1) Ingestion: fetch → validate → write `raw_trades` → heartbeat (`process=ingestion`).
2) Analytics: resume from last `derived_metrics.window_end` (or earliest trade) → build windows → compute metrics/events → upsert → heartbeat (`process=analytics`).
3) Context: harvest Finnhub news into `context_news` (configurable).
4) Summarizer: find metric windows lacking summaries → load metrics/events/context → generate summary (rules/local/cloud) → insert once → heartbeat (`process=summarizer`).

Monitoring and health
---------------------
- `ops_heartbeats`: last_seen/lag/errors per stage. Check with:
  ```sql
  SELECT * FROM ops_heartbeats;
  ```
- `ops_audit`: use `ops.audit.audit(...)` to log config/version changes as needed.

Testing
-------
After dependencies are installed:
```sh
pytest
```
If `pytest` is missing, install via `pip install pytest` or rely on `requirements.txt`.

Notes
-----
- Ingestion and analytics are idempotent via unique/upsert keys; rerunning does not duplicate rows.
- Reasoning uses deterministic rules (no LLM) so outputs are repeatable.
- Add retries/backoff to the provider if you need stronger resilience to network hiccups.
