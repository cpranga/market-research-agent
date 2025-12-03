"""
Minimal core utilities for market agent
"""
from datetime import datetime, timedelta

def get_window_bounds(ts, window_seconds):
    """
    Floor timestamp to nearest window interval.
    """
    if not isinstance(ts, datetime):
        raise ValueError("ts must be a datetime object")
    epoch = int(ts.timestamp())
    floored = epoch - (epoch % window_seconds)
    window_start = datetime.fromtimestamp(floored, ts.tzinfo)
    window_end = window_start + timedelta(seconds=window_seconds)
    return window_start, window_end
