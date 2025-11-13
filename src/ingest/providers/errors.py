"""
Shared exception base class for all market data providers.

Any provider specific failure MUST raise a ProviderError or a subclass of it.

Higher-level components catch ProviderError to handle all provider failures uniformly
"""

class ProviderError(Exception):
    """
    Base class for errors raised by any market data provider
    """
    pass