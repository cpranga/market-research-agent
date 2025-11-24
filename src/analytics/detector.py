from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from analytics.aggregator import TradeWindow
from ingest.providers.base import TradeRecord
from core.config import Config

@dataclass
class Event:
    """
    Represents a market event detected in a time window.
    
    Attributes:
        type: Event type (e.g., 'volatility_spike', 'momentum_reversal').
        severity: Severity level ('info', 'warning', 'critical').
        symbol: Market symbol for the event.
        window_start: Start timestamp of the window.
        window_end: End timestamp of the window.
        details: Optional dictionary with extra event information.
    """
    type: str
    severity: str
    symbol: str
    window_start: datetime
    window_end: datetime
    details: Optional[dict] = field(default_factory=dict)

def detect_events(
        window: TradeWindow,
        metrics: dict,
        prev_window: Optional[TradeWindow] = None,
        prev_metrics: Optional[dict] = None
) -> List[Event]:
    """
    Applies rule-based logic to metrics and windows to detect market events.
    Returns a list of Event objects for noteworthy conditions such as volatility spikes,
    momentum reversals, or abnormal price changes.

    Args:
        window: The TradeWindow being analyzed.
        metrics: Dictionary of computed metrics for the window.
        prev_window: Optional previous TradeWindow for context.
        prev_metrics: Optional metrics for the previous window.

    Returns:
        List of Event objects describing detected market events.
    """
    raised_events: List[Event] = []
    # Check for a Volatility Spike
    if metrics.get("volatility", 0.0) > Config.VOLATILITY_SPIKE_THRESHOLD:
        raised_events.append(Event(
            type="volatility_spike",
            severity="warning",
            symbol=window.symbol,
            window_start=window.window_start,
            window_end=window.window_end,
            details={"volatility": metrics.get("volatility", 0.0), "threshold": Config.VOLATILITY_SPIKE_THRESHOLD}
        ))
    
    # Check for a momentum reversal
    if prev_metrics and (metrics.get("momentum", 0.0) < 0.0) != (prev_metrics.get("momentum", 0.0) < 0.0):
        raised_events.append(Event(
            type="momentum_reversal",
            severity="info",
            symbol=window.symbol,
            window_start=window.window_start,
            window_end=window.window_end,
            details={"current": metrics.get("momentum", 0.0), "previous": prev_metrics.get("momentum", 0.0)}
        ))
    
    # Check for an abnormal price change
    if window.open_price is not None and window.close_price is not None and abs(window.close_price - window.open_price) > Config.ABNORMAL_PRICE_CHANGE_THRESHOLD:
        raised_events.append(Event(
            type="abnormal_price_change",
            severity="critical",
            symbol=window.symbol,
            window_start=window.window_start,
            window_end=window.window_end,
            details={"price_change": abs(window.close_price - window.open_price), "open_price": window.open_price, "close_price": window.close_price}
        ))
    return raised_events