import pytest
from unittest.mock import MagicMock, patch

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


# This test checks that writing an empty list immediately returns 0
# and does not try to touch the database.
@patch("psycopg2.connect")
def test_writer_empty_list(mock_connect):
    out = write([])
    assert out == 0
    mock_connect.assert_not_called()


# This test verifies the normal flow:
# - symbol exists
# - no insertion into symbols
# - ingested_data receives one insert
@patch("psycopg2.connect")
def test_writer_inserts_existing_symbol(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # SELECT symbol returns an existing id
    mock_cur.fetchone.return_value = (42,)

    rec = make_rec("AAPL")
    out = write([rec])

    # Should write exactly one row
    assert out == 1

    # First call: SELECT id FROM symbols
    # Second call: INSERT into ingested_data
    assert mock_cur.execute.call_count == 2

    # First command is symbol lookup
    call1 = mock_cur.execute.call_args_list[0]
    assert "SELECT id FROM symbols" in call1[0][0]
    assert call1[0][1] == ("AAPL",)

    # Second is ingested_data insert
    call2 = mock_cur.execute.call_args_list[1]
    assert "INSERT INTO ingested_data" in call2[0][0]


# This test verifies that a missing symbol triggers:
# - INSERT INTO symbols
# - RETURNING id
# - then insert into ingested_data using that id
@patch("psycopg2.connect")
def test_writer_inserts_new_symbol(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # First SELECT returns None (symbol missing)
    # Next fetchone() is returning id from INSERT RETURNING
    mock_cur.fetchone.side_effect = [
        None,     # SELECT id for missing symbol
        (99,)     # RETURNING id from symbol insert
    ]

    rec = make_rec("MSFT")
    out = write([rec])

    assert out == 1

    # Symbol lookup + symbol insert + ingested_data insert = 3 execute calls
    assert mock_cur.execute.call_count == 3

    # Check first call is symbol lookup
    lookup_call = mock_cur.execute.call_args_list[0]
    assert "SELECT id FROM symbols" in lookup_call[0][0]

    # Check second call inserts symbol
    insert_symbol_call = mock_cur.execute.call_args_list[1]
    assert "INSERT INTO symbols" in insert_symbol_call[0][0]

    # Check third call inserts ingested_data row
    data_insert_call = mock_cur.execute.call_args_list[2]
    assert "INSERT INTO ingested_data" in data_insert_call[0][0]


# This test checks that repeated symbols in the same batch only perform
# one lookup/insert, thanks to symbol caching.
@patch("psycopg2.connect")
def test_writer_symbol_caching(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # First SELECT -> missing
    # Then INSERT RETURNING
    mock_cur.fetchone.side_effect = [
        None,   # first symbol lookup (missing)
        (10,),  # inserted symbol id
    ]

    rec1 = make_rec("AAPL")
    rec2 = make_rec("AAPL")

    out = write([rec1, rec2])
    assert out == 2

    # Lookup, insert symbol, then two ingested_data inserts
    # Total = 1 select + 1 insert symbol + 2 inserts = 4 executes
    assert mock_cur.execute.call_count == 4

    # Confirm no second SELECT for the same symbol
    select_calls = [
        call for call in mock_cur.execute.call_args_list
        if "SELECT id FROM symbols" in call[0][0]
    ]
    assert len(select_calls) == 1


# This test checks that a psycopg2 error is converted into WriterError
@patch("psycopg2.connect")
def test_writer_db_error_raises_writererror(mock_connect):
    mock_connect.side_effect = Exception("connection failed")

    with pytest.raises(WriterError):
        write([make_rec()])


# This test checks that ingested_data insert failure is handled properly.
# We simulate the first SELECT returning a symbol id, then failing on insert.
@patch("psycopg2.connect")
def test_writer_insert_failure(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # First fetchone returns symbol_id
    mock_cur.fetchone.return_value = (7,)

    # Next execute (data insert) throws a psycopg2.Error
    mock_cur.execute.side_effect = [
        None,  # SELECT symbol_id
        Exception("db insert error")  # fail on insert
    ]

    with pytest.raises(WriterError):
        write([make_rec("AAPL")])
