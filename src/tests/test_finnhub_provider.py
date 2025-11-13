import pytest
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock

from ingest.providers.finnhub_provider import FinnhubProvider, FinnhubError
from ingest.providers.base import TradeRecord


# This helper sets up a provider with a test API key.
# We patch the environment so the provider always sees a valid key.
@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "TESTKEY")
    return FinnhubProvider(api_key="TESTKEY")


# This test checks that a normal, successful Finnhub response
# produces exactly one TradeRecord with the expected values.
@patch("requests.get")
def test_successful_fetch(mock_get, provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "c": 123.45,
        "v": 10
    }
    mock_get.return_value = mock_response

    record = provider.fetch("AAPL")

    assert isinstance(record, TradeRecord)
    assert record.symbol == "AAPL"
    assert record.price == 123.45
    assert record.size == 10
    assert record.source == "finnhub"
    assert isinstance(record.ts, datetime)


# This test checks what happens if both the environment variable and
# the Config value for the API key are missing. The provider should fail.
def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    monkeypatch.setattr("core.config.Config.FINNHUB_API_KEY", None)

    with pytest.raises(FinnhubError):
        FinnhubProvider(api_key=None)


# This test checks that the provider raises an error when Finnhub returns
# a non-200 status code, such as 403 or 500.
@patch("requests.get")
def test_http_error_status(mock_get, provider):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Forbidden"
    mock_get.return_value = mock_resp

    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")


# These tests check how the provider handles basic networking errors.
# If the request times out or cannot connect, it should raise FinnhubError.
@patch("requests.get")
def test_timeout_error(mock_get, provider):
    mock_get.side_effect = requests.exceptions.Timeout("timeout")
    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")


@patch("requests.get")
def test_connection_error(mock_get, provider):
    mock_get.side_effect = requests.exceptions.ConnectionError("conn-error")
    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")


# This test checks that if the response cannot be parsed as JSON,
# the provider raises an error instead of crashing.
@patch("requests.get")
def test_invalid_json(mock_get, provider):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("bad json")
    mock_get.return_value = mock_resp

    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")


# These tests check that the provider handles missing or invalid prices.
# Finnhub is expected to return the price in the field "c". If it is missing,
# null, or zero, the provider should raise an error.
@patch("requests.get")
def test_missing_price_field(mock_get, provider):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "v": 100
    }
    mock_get.return_value = mock_resp

    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")


@patch("requests.get")
def test_zero_price_invalid(mock_get, provider):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "c": 0,
        "v": 10
    }
    mock_get.return_value = mock_resp

    with pytest.raises(FinnhubError):
        provider.fetch("AAPL")
