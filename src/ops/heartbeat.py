"""
Heartbeat ops wrapper for market agent
"""
from core.db import log_heartbeat

async def heartbeat(process, lag_seconds=0.0, errors=0):
    await log_heartbeat(process, lag_seconds, errors)
