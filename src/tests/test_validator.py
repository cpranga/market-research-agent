import pytest
from datetime import datetime, timedelta, timezone

from ingest.validator import validate
from ingest.providers.base import TradeRecord


# Helper to create records quickly
def make_record(symbol="AAPL", price=100.0, size=10.0, ts=None, source="finnhub"):
    if ts is None:
        ts = datetime.now(timezone.utc)
    return TradeRecord(
        symbol=symbol,
        ts=ts,
        price=price,
        size=size,
        source=source
    )


# This test checks that valid input is returned unchanged.
def test_validate_happy_path():
    rec = make_record()
    out = validate([rec])
    assert out == [rec]


# This test checks that size=None is normalized to 0.
def test_size_none_normalizes_to_zero():
    rec = make_record(size=None)
    out = validate([rec])
    assert out[0].size == 0


# This test checks that negative sizes are normalized.
def test_size_negative_normalizes():
    rec = make_record(size=-5)
    out = validate([rec])
    assert out[0].size == 0


# This test checks that an empty list returns an empty list.
def test_validate_empty_list():
    assert validate([]) == []


# This test checks that a record missing a symbol triggers an error.
def test_missing_symbol_raises():
    rec = make_record(symbol="")
    with pytest.raises(ValueError):
        validate([rec])


# This test checks that a naive timestamp (no timezone) triggers an error.
def test_naive_timestamp_raises():
    ts = datetime(2024, 1, 1, 12, 0, 0)  # no timezone info
    rec = make_record(ts=ts)
    with pytest.raises(ValueError):
        validate([rec])


# This test checks that timestamps far in the future are rejected.
def test_future_timestamp_raises():
    future_ts = datetime.now(timezone.utc) + timedelta(days=2)
    rec = make_record(ts=future_ts)
    with pytest.raises(ValueError):
        validate([rec])


# This test checks that price <= 0 triggers an error.
def test_invalid_price_raises():
    rec = make_record(price=0)
    with pytest.raises(ValueError):
        validate([rec])


# This test checks that price cannot be negative.
def test_negative_price_raises():
    rec = make_record(price=-5)
    with pytest.raises(ValueError):
        validate([rec])


# This test checks that duplicates (same symbol + timestamp) are removed.
def test_duplicate_records_removed():
    ts = datetime.now(timezone.utc)
    rec1 = make_record(ts=ts)
    rec2 = make_record(ts=ts)
    out = validate([rec1, rec2])
    assert out == [rec1]


# This test checks that the validator raises if the record type is wrong.
def test_invalid_record_type_raises():
    with pytest.raises(ValueError):
        validate(["not a trade record"])


# This test checks that source must be a non-empty string.
def test_missing_source_raises():
    ts = datetime.now(timezone.utc)
    rec = TradeRecord("AAPL", ts, 100.0, 10.0, None)
    with pytest.raises(ValueError):
        validate([rec])


# This test ensures ordering is preserved.
def test_validator_preserves_order():
    ts1 = datetime.now(timezone.utc)
    ts2 = datetime.now(timezone.utc) - timedelta(seconds=5)
    rec1 = make_record(symbol="AAPL", ts=ts1)
    rec2 = make_record(symbol="MSFT", ts=ts2)
    out = validate([rec1, rec2])
    assert out == [rec1, rec2]
