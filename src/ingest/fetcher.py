from typing import List
import time

from core.config import Config
from ingest.providers import get_provider
from ingest.providers.base import TradeRecord
from ingest.providers.errors import ProviderError


def fetch_all() -> List[TradeRecord]:
    provider = get_provider()
    trade_records: List[TradeRecord] = []
    for i, symbol in enumerate(Config.SYMBOLS):
        # Implicitly re-raises any thrown errors
        record: TradeRecord = provider.fetch(symbol)
        trade_records.append(record)
        if i < len(Config.SYMBOLS) - 1:
            time.sleep(Config.REQUEST_DELAY)
    return trade_records