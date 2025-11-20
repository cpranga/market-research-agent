-- ==========================================================
-- Market Agent: Unified Schema
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================================
-- Core data tables
-- ==========================================================
CREATE TABLE IF NOT EXISTS raw_trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          TEXT NOT NULL,
    ts              TIMESTAMPTZ NOT NULL,
    price           NUMERIC(18,6) NOT NULL,
    size            NUMERIC(18,6),
    source          TEXT,
    inserted_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_trades_symbol_ts
    ON raw_trades(symbol, ts);

-- ==========================================================
-- Derived metrics and events
-- ==========================================================
CREATE TABLE IF NOT EXISTS derived_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          TEXT NOT NULL,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    vwap            NUMERIC(18,6),
    volatility      NUMERIC(18,6),
    momentum        NUMERIC(18,6),
    liquidity_ratio NUMERIC(18,6),
    computed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_symbol_window
    ON derived_metrics(symbol, window_start, window_end);

CREATE TABLE IF NOT EXISTS events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          TEXT NOT NULL,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    type            TEXT NOT NULL,
    severity        TEXT,
    details         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_symbol_window
    ON events(symbol, window_start, window_end);

-- ==========================================================
-- External context (news, sector, market)
-- ==========================================================
CREATE TABLE IF NOT EXISTS context_news (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          TEXT,
    published_at    TIMESTAMPTZ,
    title           TEXT,
    summary         TEXT,
    hash            TEXT UNIQUE,
    source          TEXT,
    inserted_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_symbol_ts
    ON context_news(symbol, published_at DESC);

CREATE TABLE IF NOT EXISTS context_sector (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sector_id       TEXT,
    window_start    TIMESTAMPTZ,
    window_end      TIMESTAMPTZ,
    avg_return      NUMERIC(18,6),
    avg_volatility  NUMERIC(18,6),
    inserted_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS context_market (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    window_start    TIMESTAMPTZ,
    window_end      TIMESTAMPTZ,
    spx_return      NUMERIC(18,6),
    vix_level       NUMERIC(18,6),
    risk_flag       TEXT,
    inserted_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================
-- Reasoning and text outputs
-- ==========================================================
CREATE TABLE IF NOT EXISTS summaries (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol           TEXT NOT NULL,
    window_start     TIMESTAMPTZ NOT NULL,
    window_end       TIMESTAMPTZ NOT NULL,
    model            TEXT,
    prompt_version   TEXT,
    text             TEXT,
    tokens_used      INTEGER,
    latency_ms       INTEGER,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_summaries_symbol_window
    ON summaries(symbol, window_start, window_end);

CREATE TABLE IF NOT EXISTS model_registry (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name       TEXT NOT NULL,
    provider         TEXT,
    version          TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             TEXT NOT NULL,
    version          TEXT,
    content          TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================
-- Metadata & Operations
-- ==========================================================
CREATE TABLE IF NOT EXISTS ops_audit (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    who             TEXT,
    what            TEXT,
    old_value       JSONB,
    new_value       JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_heartbeats (
    process         TEXT PRIMARY KEY,
    last_seen       TIMESTAMPTZ NOT NULL,
    lag_seconds     NUMERIC(10,2),
    errors          INTEGER DEFAULT 0,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
