import pytest
from unittest.mock import patch, MagicMock

from ingest.fetcher import fetch_all
from ingest.providers.base import TradeRecord
from ingest.providers.errors import ProviderError


# This test checks that fetch_all() calls provider.fetch() once
# for each symbol and returns the records in the same order.
@patch("ingest.fetcher.get_provider")
@patch("ingest.fetcher.Config")
def test_fetcher_returns_records_in_order(mock_config, mock_get_provider):
    mock_config.SYMBOLS = ["AAPL", "MSFT", "GOOG"]
    mock_config.REQUEST_DELAY = 0.0  # no sleeping during this test

    mock_provider = MagicMock()
    mock_get_provider.return_value = mock_provider

    # Create three fake TradeRecord objects
    rec1 = MagicMock(spec=TradeRecord)
    rec2 = MagicMock(spec=TradeRecord)
    rec3 = MagicMock(spec=TradeRecord)

    # Each call to provider.fetch() should return one of the above
    mock_provider.fetch.side_effect = [rec1, rec2, rec3]

    records = fetch_all()

    assert records == [rec1, rec2, rec3]
    assert mock_provider.fetch.call_count == 3
    assert mock_provider.fetch.call_args_list[0][0][0] == "AAPL"
    assert mock_provider.fetch.call_args_list[1][0][0] == "MSFT"
    assert mock_provider.fetch.call_args_list[2][0][0] == "GOOG"


# This test checks that if provider.fetch() raises a ProviderError,
# fetch_all() should immediately raise the same error.
@patch("ingest.fetcher.get_provider")
@patch("ingest.fetcher.Config")
def test_fetcher_propagates_provider_error(mock_config, mock_get_provider):
    mock_config.SYMBOLS = ["AAPL", "MSFT"]
    mock_config.REQUEST_DELAY = 0.0

    mock_provider = MagicMock()
    mock_get_provider.return_value = mock_provider

    mock_provider.fetch.side_effect = ProviderError("Failed to fetch AAPL")

    with pytest.raises(ProviderError):
        fetch_all()

    # Ensure it stopped after the first failure
    assert mock_provider.fetch.call_count == 1


# This test verifies that the fetcher respects the pacing delay between
# symbol fetch calls by checking that time.sleep() is called.
@patch("ingest.fetcher.get_provider")
@patch("ingest.fetcher.time")
@patch("ingest.fetcher.Config")
def test_fetcher_calls_sleep_between_symbols(mock_config, mock_time, mock_get_provider):
    mock_config.SYMBOLS = ["AAPL", "MSFT", "GOOG"]
    mock_config.REQUEST_DELAY = 0.25

    mock_provider = MagicMock()
    mock_get_provider.return_value = mock_provider

    # Make provider.fetch() return a valid TradeRecord for each symbol
    rec = MagicMock(spec=TradeRecord)
    mock_provider.fetch.return_value = rec

    fetch_all()

    # sleep should have been called once per gap between symbols
    # If there are 3 symbols, there should be 2 sleep calls.
    assert mock_time.sleep.call_count == 2

    # Each call to sleep() should use the configured delay
    for call in mock_time.sleep.call_args_list:
        assert call[0][0] == 0.25


# This test checks that fetch_all() returns an empty list if
# SYMBOLS is configured as an empty list.
@patch("ingest.fetcher.get_provider")
@patch("ingest.fetcher.Config")
def test_fetcher_with_no_symbols(mock_config, mock_get_provider):
    mock_config.SYMBOLS = []
    mock_config.REQUEST_DELAY = 0.0

    mock_provider = MagicMock()
    mock_get_provider.return_value = mock_provider

    records = fetch_all()

    assert records == []
    assert mock_provider.fetch.call_count == 0
