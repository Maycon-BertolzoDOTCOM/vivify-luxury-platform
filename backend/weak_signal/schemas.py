"""Data schemas for weak signal monitoring."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class MonitoredTarget(BaseModel):
    target_id: str = ""
    handle: str
    platform: str = ""
    queries: list[str] = Field(default_factory=list)
    cadence: str = "daily"
    alert_threshold: float = 0.6
    enabled: bool = True


class SignalRecord(BaseModel):
    target_id: str
    handle: str
    platform: str
    text: str
    topics: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
