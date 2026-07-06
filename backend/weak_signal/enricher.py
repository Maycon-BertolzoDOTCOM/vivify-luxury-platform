"""Signal enricher — pass-through for now."""
from __future__ import annotations

from typing import Any


class SignalEnricher:
    def enrich_batch(self, records: list[Any]) -> list[Any]:
        return records
