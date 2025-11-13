"""
Provider interface for market data sources

This module defines:
- TradeRecord: the normalized shape of each trade/bar record
- BaseProvider: an abstract interface that all providers must implement
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class TradeRecord:
    """
    Normalized market data record
    
    All providers must return data in this shape
    """
    symbol: str
    ts: datetime
    price: float
    size: float
    source: str

class BaseProvider(ABC):
    """
    Abstract base class for all market data providers.
    """
    
    @abstractmethod
    def fetch(self, symbol: str) -> TradeRecord:
        """
        Fetch recent information for a given symbol.
        
        Implementations:
        - Decide the exact lookback / window (config driven)
        - Normalize all records into TradeRecord
        - Handle provider-specific errors and raise or log
        """
        raise NotImplementedError