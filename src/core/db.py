"""
Database Access Layer

Provides a centralized, minimal, and reliable interface for interacting with the PostgreSQL database.
This module abstracts connection creation, pooled access, and query execution so that ingest, analytics,
and reasoning modules never directly manage psycopg2 or asyncpg.
"""
from typing import List, Dict, Any, Optional
import asyncpg

from core.config import Config

pool: Optional[asyncpg.pool.Pool] = None

async def init_pool():
    """
    Create a global asyncpg connection pool.
    Should be called once during application startup.
    """
    global pool
    if pool is not None:
        return
    
    if not Config.DB_URL:
        raise RuntimeError("DB_URL is not set.")
    
    pool = await asyncpg.create_pool(
        dsn=Config.DB_URL,
        min_size=1,
        max_size=5,
    )

async def fetch(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query and returns rows as a list of dictionaries.
    Caller is responsible for passing safe SQL and Parameters.
    """
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]

async def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Same as fetch(), but returns either one row or None
    """
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *params)
        return dict(row) if row else None

async def execute(sql: str, params: tuple = ()) -> None:
    """
    Execute INSERT/UPDATE/Delete.
    Does not return rows
    """
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    
    async with pool.acquire() as conn:
        await conn.execute(sql, *params)

async def close_pool():
    """
    Gracefully closes the database pool.
    """
    global pool
    if pool is not None:
        await pool.close()
        pool = None