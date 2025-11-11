-- ==========================================================
-- 001_init.sql : Derived metrics and events
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
