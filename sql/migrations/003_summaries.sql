-- ==========================================================
-- 003_summaries.sql : Reasoning and text outputs
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
