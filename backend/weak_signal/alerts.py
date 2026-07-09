"""Alert management — real in-memory storage with file log channel."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel

logger = logging.getLogger("vivify.weak_signal.alerts")


class AlertRecord(BaseModel):
    alert_id: str
    target_id: str
    message: str
    severity: str = "info"
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class FileLogChannel:
    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("VIVIFY_ALERT_LOG", "/tmp/vivify_alerts.log")

    def write(self, record: AlertRecord) -> None:
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(record.model_dump(), default=str) + "\n")
        except OSError as e:
            logger.warning("Failed to write alert to %s: %s", self.path, e)


class AlertManager:
    def __init__(self, channels: Optional[list[Any]] = None):
        self.channels = channels or []
        self._alerts: list[AlertRecord] = []

    def emit(
        self,
        target_id: str,
        message: str,
        severity: str = "info",
    ) -> AlertRecord:
        record = AlertRecord(
            alert_id=uuid4().hex[:12],
            target_id=target_id,
            message=message,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._alerts.append(record)
        for ch in self.channels:
            try:
                ch.write(record)
            except Exception as e:
                logger.warning("Alert channel failed: %s", e)
        return record

    def history(self, limit: int = 50, target_id: str = "") -> list[AlertRecord]:
        results = list(self._alerts)
        if target_id:
            results = [a for a in results if a.target_id == target_id]
        results.sort(key=lambda a: a.timestamp, reverse=True)
        return results[:limit]
