"""
Monitor ops wrapper for market agent
"""
from core.db import get_lag

async def get_stage_lag(process):
    return await get_lag(process)
