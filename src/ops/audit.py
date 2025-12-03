"""
Audit ops wrapper for market agent
"""
from core.db import log_audit

async def audit(who, what, old_value, new_value):
    await log_audit(who, what, old_value, new_value)
