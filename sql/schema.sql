-- ==========================================================
-- Market Agent: Base Schema
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core data tables
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
