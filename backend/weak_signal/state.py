"""In-memory signal state store."""
from __future__ import annotations

from typing import Optional

from .schemas import SignalRecord


class SignalState:
    def __init__(self):
        self._records: list[SignalRecord] = []

    def store(self, record: SignalRecord) -> None:
        self._records.append(record)

    def query(
        self,
        handle: str,
        platform: str,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> list[SignalRecord]:
        results = [
            r for r in self._records
            if r.handle == handle and r.platform == platform
        ]
        if since:
            results = [r for r in results if r.timestamp >= since]
        results.sort(key=lambda r: r.timestamp, reverse=True)
        return results[:limit]
