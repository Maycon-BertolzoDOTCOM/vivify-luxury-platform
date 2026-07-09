"""Anomaly detection — real z-score based detector with rolling windows."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel

from .schemas import SignalRecord

_JEWELRY_KEYWORDS = [
    "ouro", "prata", "platina", "rose gold", "ouro branco", "ouro amarelo",
    "diamante", "esmeralda", "safira", "rubi", "moissanite", "opala", "zircônia",
    "minimalist", "vintage", "modern", "custom", "clássico",
    "lab grown", "gold price", "price surge", "sustainable",
    "noivo", "noiva", "casamento", "aliança", "anel", "colar", "brinco", "pulseira",
]


class AnomalyReport(BaseModel):
    target_id: str
    signal_count: int = 0
    anomaly_count: int = 0
    anomalies: list[dict[str, Any]] = []
    score: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class AnomalyDetector:
    def __init__(
        self,
        state: Optional[Any] = None,
        std_multiplier: float = 2.0,
        window_size: int = 10,
    ):
        self.state = state
        self.std_multiplier = std_multiplier
        self.window_size = window_size
        self._keyword_history: dict[str, list[int]] = defaultdict(list)

    def _extract_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in _JEWELRY_KEYWORDS if kw in text_lower]

    def _z_score(self, values: list[int], value: int) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        if variance == 0:
            return 0.0
        std = math.sqrt(variance)
        return (value - mean) / std

    def detect(self, target_id: str, records: list[SignalRecord]) -> AnomalyReport:
        anomalies = []
        keyword_counts: dict[str, int] = {}

        for rec in records:
            texts = [rec.text] if isinstance(rec, SignalRecord) else [rec.get("text", "")]
            for text in texts:
                for kw in self._extract_keywords(text):
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        total_anomalies = 0
        max_z = 0.0
        for kw, count in keyword_counts.items():
            key = f"{target_id}:{kw}"
            history = self._keyword_history[key]
            history.append(count)
            if len(history) > self.window_size:
                history.pop(0)

            z = self._z_score(history[:-1], count) if len(history) > 1 else 0.0
            max_z = max(max_z, z)

            if z > self.std_multiplier:
                total_anomalies += 1
                anomalies.append({
                    "keyword": kw,
                    "count": count,
                    "z_score": round(z, 2),
                    "mean": round(sum(history[:-1]) / max(len(history) - 1, 1), 2) if len(history) > 1 else 0.0,
                    "target_id": target_id,
                })

        return AnomalyReport(
            target_id=target_id,
            signal_count=len(records),
            anomaly_count=total_anomalies,
            anomalies=anomalies,
            score=round(min(max_z / 5.0, 1.0), 4),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
