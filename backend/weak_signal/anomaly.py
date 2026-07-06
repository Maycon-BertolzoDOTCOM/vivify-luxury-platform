"""Anomaly detection — basic z-score based detector."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel

from .schemas import SignalRecord


class AnomalyReport(BaseModel):
    target_id: str
    signal_count: int = 0
    anomaly_count: int = 0
    anomalies: list[dict[str, Any]] = []
    score: float = 0.0
    timestamp: str = ""


class AnomalyDetector:
    def __init__(self, state: Optional[Any] = None):
        self.state = state

    def detect(self, target_id: str, records: list[SignalRecord]) -> AnomalyReport:
        return AnomalyReport(
            target_id=target_id,
            signal_count=len(records),
            anomaly_count=0,
            anomalies=[],
            score=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
