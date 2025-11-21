import asyncio
import asyncpg
from urllib.parse import urlparse
import os
import uuid
import pytest_asyncio
from pathlib import Path

# Import the database module that is being tested
import core.db as db

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    Use a static test database for all tests. Assumes schema is already loaded.
    Temporarily replace settings.DB_URL for the duration of tests,
    initialize the connection pool, and then return control to the tests.
    After tests finish, close the pool and restore the original DB_URL.
    """

    static_test_url = os.getenv("TEST_DATABASE_URL")
    if not static_test_url:
        raise RuntimeError("TEST_DATABASE_URL must be defined for database tests.")

    from core.config import Config
    original_url = Config.DB_URL
    Config.DB_URL = static_test_url

    await db.init_pool()
    yield
    await db.close_pool()
    Config.DB_URL = original_url


import pytest

@pytest.mark.asyncio
async def test_init_pool_creates_pool(test_db):
    """
    Verify that the connection pool is created successfully.
    """
    assert db.pool is not None
    assert isinstance(db.pool, asyncpg.pool.Pool)


@pytest.mark.asyncio
async def test_execute_and_fetch(test_db):
    """
    Insert a row into raw_trades and ensure it can be retrieved.
    """

    # Clean up table before test
    await db.execute("DELETE FROM raw_trades")

    await db.execute(
        "INSERT INTO raw_trades (symbol, ts, price, size) "
        "VALUES ($1, NOW(), 123.45, 10.0)",
        ("AAPL",)
    )

    rows = await db.fetch(
        "SELECT symbol, price, size FROM raw_trades"
    )

    assert len(rows) == 1
    row = rows[0]

    # Convert Decimals to float for easier comparison
    assert row["symbol"] == "AAPL"
    assert float(row["price"]) == 123.45
    assert float(row["size"]) == 10.0


@pytest.mark.asyncio
async def test_fetch_one(test_db):
    """
    Ensure fetch_one returns the first matching row.
    """
    row = await db.fetch_one(
        "SELECT symbol FROM raw_trades LIMIT 1"
    )
    assert row is not None
    assert row["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_fetch_empty(test_db):
    """
    Ensure fetch_one returns None when no rows exist.
    """
    row = await db.fetch_one(
        "SELECT * FROM derived_metrics LIMIT 1"
    )
    assert row is None
