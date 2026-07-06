"""In-memory target registry."""
from __future__ import annotations

from .schemas import MonitoredTarget


class SignalRegistry:
    def __init__(self):
        self._targets: list[MonitoredTarget] = []

    def add(self, target: MonitoredTarget) -> None:
        self._targets.append(target)

    def list_all(self, enabled_only: bool = True) -> list[MonitoredTarget]:
        if enabled_only:
            return [t for t in self._targets if t.enabled]
        return list(self._targets)
