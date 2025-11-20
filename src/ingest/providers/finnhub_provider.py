from typing import Optional
import requests
from datetime import datetime, timezone

from core.config import Config
from ingest.providers.base import BaseProvider, TradeRecord
from ingest.providers.errors import ProviderError

class FinnhubError(ProviderError):
    """
    Errors raised specifically by the Finnhub provider
    """
    pass

class FinnhubProvider(BaseProvider):
    QUOTE_URL = "https://finnhub.io/api/v1/quote"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.FINNHUB_API_KEY
        if not self.api_key or self.api_key is None:
            raise FinnhubError("Finnhub API Key is missing.")
        
    def fetch(self, symbol: str) -> TradeRecord:
        # Build the request
        params = {
            "token": self.api_key,
            "symbol": symbol,
        }

        try:
            response = requests.get(self.QUOTE_URL, params=params, timeout=5)

        except requests.exceptions.Timeout as e:
            raise FinnhubError("Timeout when fetching {}: {}".format(symbol, e))
        
        except requests.exceptions.ConnectionError as e:
            raise FinnhubError("Connection error when fetching {}: {}".format(symbol, e))
        
        except requests.exceptions.RequestException as e:
            raise FinnhubError("HTTP Error when fetching {}: {}".format(symbol, e))
        
        # Handle non-200 status
        if response.status_code != 200:
            raise FinnhubError(
                "Finnhub returned {} for symbol {}: {}".format(
                    response.status_code,
                    symbol,
                    response.text[:200],
                )
            )
        
        # Parse JSON
        try:
            data: dict = response.json()
        except ValueError:
            raise FinnhubError(
                "Invalid JSON from Finnhub for {}: {}".format(
                    symbol,
                    response.text[:200],
                )
            )

        # Validate content
        if data.get("c", "") in (None, 0, "", "0"):
            raise FinnhubError(
                "Finnhub returned missing or invalid price for {}. Response: {}".format(
                    symbol,
                    data,
                )
            )
        
        # Build and return TradeRecord
        price = float(data["c"])
        size = float(data.get("v", 0))

        return TradeRecord(
            symbol=symbol,
            ts=datetime.now(timezone.utc),
            price=price,
            size=size,
            source="finnhub",
        )