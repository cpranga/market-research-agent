"""
Provider factory for market data ingestion

This module exposes one function: get_provider()

It reads Config.API_PROVIDER and returns the correct provider instance.
If an unknown provider is requested, it returns a ProviderError
"""

from core.config import Config
from ingest.providers.errors import ProviderError
from ingest.providers.finnhub_provider import FinnhubProvider

def get_provider():
    """
    Return an instance of the provider specified in Config.API_PROVIDER
    
    Supported values:
    - "finnhub"
    
    If the config contains an unsupported provider name, this function returns
    and error
    """

    provider_name = (Config.API_PROVIDER or "").lower()

    if provider_name == "finnhub":
        return FinnhubProvider()
    
    raise ProviderError(
        "Unknown API Provider '{}'. Supported providers: finnhub.".format(
            provider_name
        )
    )