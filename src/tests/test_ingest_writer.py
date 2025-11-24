
import pytest
from unittest.mock import AsyncMock, patch

from ingest.writer import write
from ingest.writer_errors import WriterError
from ingest.providers.base import TradeRecord
from datetime import datetime, timezone

def make_rec(symbol="AAPL", price=100.0, size=10.0):
    return TradeRecord(
        symbol=symbol,
        ts=datetime.now(timezone.utc),
        price=price,
        size=size,
        source="finnhub"
    )

# Test writing an empty list returns 0 and does not call db.execute
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_empty_list(mock_execute):
    out = await write([])
    assert out == 0
    mock_execute.assert_not_called()

# Test single row insert
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_inserts_single_row(mock_execute):
    rec = make_rec("AAPL")
    out = await write([rec])
    assert out == 1
    mock_execute.assert_awaited_once()
    sql = mock_execute.call_args[0][0]
    assert "INSERT INTO raw_trades" in sql

# Test multiple row inserts
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_inserts_multiple_rows(mock_execute):
    rec1 = make_rec("AAPL")
    rec2 = make_rec("MSFT")
    out = await write([rec1, rec2])
    assert out == 2
    assert mock_execute.await_count == 2
    for call in mock_execute.call_args_list:
        sql = call[0][0]
        assert "INSERT INTO raw_trades" in sql

# Test duplicate symbol inserts
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_inserts_duplicate_symbols(mock_execute):
    rec1 = make_rec("AAPL")
    rec2 = make_rec("AAPL")
    out = await write([rec1, rec2])
    assert out == 2
    assert mock_execute.await_count == 2
    for call in mock_execute.call_args_list:
        sql = call[0][0]
        assert "INSERT INTO raw_trades" in sql

# Test db error raises WriterError
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_db_error_raises_writererror(mock_execute):
    mock_execute.side_effect = Exception("connection failed")
    with pytest.raises(WriterError):
        await write([make_rec()])

# Test insert failure raises WriterError
@pytest.mark.asyncio
@patch("ingest.writer.execute", new_callable=AsyncMock)
async def test_writer_insert_failure(mock_execute):
    mock_execute.side_effect = Exception("db insert error")
    with pytest.raises(WriterError):
        await write([make_rec("AAPL")])
