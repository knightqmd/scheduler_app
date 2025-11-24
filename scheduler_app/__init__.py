"""
AI-powered scheduling package.

This package bundles the data model, prompt assembly helpers, and the
client wrapper used to talk to a large language model for building schedules.
"""

from .models import ScheduleItem, UserSchedule
from .scheduler import ScheduleService

__all__ = ["ScheduleItem", "UserSchedule", "ScheduleService"]
