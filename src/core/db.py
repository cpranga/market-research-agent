"""
Database Access Layer

Provides a centralized, minimal, and reliable interface for interacting with the PostgreSQL database.
This module abstracts connection creation, pooled access, and query execution so that ingest, analytics,
and reasoning modules never directly manage psycopg2 or asyncpg.
"""
from typing import List, Dict, Any, Optional
import asyncpg
from asyncpg import exceptions as pg_exceptions

from core.config import Config

pool: Optional[asyncpg.pool.Pool] = None


async def init_pool():
    """
    Create a global asyncpg connection pool.
    Should be called once during application startup or if the pool has been closed.
    """
    global pool
    if pool is not None and not getattr(pool, "_closed", False):
        return
    
    if not Config.DB_URL:
        raise RuntimeError("DB_URL is not set.")
    
    pool = await asyncpg.create_pool(
        dsn=Config.DB_URL,
        min_size=1,
        max_size=5,
    )
    # Ensure required unique index for ingestion idempotency exists
    async with pool.acquire() as conn:
        await conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS raw_trades_symbol_ts_key ON raw_trades(symbol, ts)"
        )

async def fetch(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query and returns rows as a list of dictionaries.
    Caller is responsible for passing safe SQL and Parameters.
    """
    if pool is None or getattr(pool, "_closed", False):
        await init_pool()

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(r) for r in rows]
    except pg_exceptions.InterfaceError:
        await init_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(r) for r in rows]

async def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Same as fetch(), but returns either one row or None
    """
    if pool is None or getattr(pool, "_closed", False):
        await init_pool()
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
            return dict(row) if row else None
    except pg_exceptions.InterfaceError:
        await init_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
            return dict(row) if row else None

async def execute(sql: str, params: tuple = ()) -> None:
    """
    Execute INSERT/UPDATE/Delete.
    Does not return rows
    """
    if pool is None or getattr(pool, "_closed", False):
        await init_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute(sql, *params)
    except pg_exceptions.InterfaceError:
        await init_pool()
        async with pool.acquire() as conn:
            await conn.execute(sql, *params)




async def log_heartbeat(process: str, lag_seconds: float = 0.0, errors: int = 0):
    """
    Log a heartbeat for a pipeline process.
    """
    await execute(
        """
        INSERT INTO ops_heartbeats (process, last_seen, lag_seconds, errors, updated_at)
        VALUES ($1, NOW(), $2, $3, NOW())
        ON CONFLICT (process) DO UPDATE SET
            last_seen = EXCLUDED.last_seen,
            lag_seconds = EXCLUDED.lag_seconds,
            errors = ops_heartbeats.errors + EXCLUDED.errors,
            updated_at = EXCLUDED.updated_at;
        """,
        (process, lag_seconds, errors)
    )

async def log_audit(who: str, what: str, old_value, new_value):
    """
    Log an audit event.
    """
    await execute(
        """
        INSERT INTO ops_audit (who, what, old_value, new_value, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        """,
        (who, what, old_value, new_value)
    )

async def executemany(sql: str, seq_of_params):
    """
    Execute many statements in a batch.
    """
    if pool is None or getattr(pool, "_closed", False):
        await init_pool()
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                for params in seq_of_params:
                    await conn.execute(sql, *params)
    except pg_exceptions.InterfaceError:
        await init_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for params in seq_of_params:
                    await conn.execute(sql, *params)

async def get_lag(process: str) -> float:
    """
    Get lag_seconds for a process from ops_heartbeats.
    """
    row = await fetch_one(
        "SELECT lag_seconds FROM ops_heartbeats WHERE process = $1", (process,)
    )
    if row and row.get("lag_seconds") is not None:
        return row["lag_seconds"]
    return -1.0

async def close_pool():
    """
    Gracefully closes the database pool.
    """
    global pool
    if pool is not None:
        await pool.close()
        pool = None
