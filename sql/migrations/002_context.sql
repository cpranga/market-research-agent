-- ==========================================================
-- 002_context.sql : External context (news, sector, market)
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
