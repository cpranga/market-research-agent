import pytest
from unittest.mock import patch

from ingest.providers import get_provider
from ingest.providers.finnhub_provider import FinnhubProvider
from ingest.providers.errors import ProviderError


# This test checks that when API_PROVIDER is set to "finnhub",
# the factory returns a FinnhubProvider instance.
def test_factory_returns_finnhub(monkeypatch):
    monkeypatch.setattr("core.config.Config.API_PROVIDER", "finnhub")
    provider = get_provider()
    assert isinstance(provider, FinnhubProvider)


# This test makes sure the provider lookup is case-insensitive.
def test_factory_case_insensitive(monkeypatch):
    monkeypatch.setattr("core.config.Config.API_PROVIDER", "FiNnHuB")
    provider = get_provider()
    assert isinstance(provider, FinnhubProvider)


# This test checks that if the provider name is not recognized,
# the factory raises a ProviderError.
def test_factory_unknown_provider(monkeypatch):
    monkeypatch.setattr("core.config.Config.API_PROVIDER", "unknownprovider")
    with pytest.raises(ProviderError):
        get_provider()


# This test checks that an empty provider name also triggers an error.
def test_factory_no_provider(monkeypatch):
    monkeypatch.setattr("core.config.Config.API_PROVIDER", "")
    with pytest.raises(ProviderError):
        get_provider()


# This test checks that None behaves the same way as missing config.
def test_factory_none_provider(monkeypatch):
    monkeypatch.setattr("core.config.Config.API_PROVIDER", None)
    with pytest.raises(ProviderError):
        get_provider()
