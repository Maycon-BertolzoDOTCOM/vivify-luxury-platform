"""Trends service — wraps TRACTION weak signal detection for jewelry market intelligence."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import sys
from pathlib import Path

TRAMA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "trama"
TRACTION_PATH = Path(__file__).resolve().parent.parent.parent.parent / "traction"
sys.path.insert(0, str(TRAMA_PATH))
sys.path.insert(0, str(TRACTION_PATH))

from trama.weak_signal.schemas import MonitoredTarget, SignalRecord  # noqa: E402
from trama.weak_signal.state import SignalState  # noqa: E402
from trama.weak_signal.registry import SignalRegistry  # noqa: E402
from trama.weak_signal.enricher import SignalEnricher  # noqa: E402
from trama.weak_signal.anomaly import AnomalyDetector  # noqa: E402
from trama.weak_signal.alerts import AlertManager, AlertRecord  # noqa: E402
from trama.weak_signal.channels import FileLogChannel  # noqa: E402

logger = logging.getLogger("vivify.trends")

_JEWELRY_QUERIES = {
    "design_trends": [
        "engagement ring trends",
        "custom jewelry design",
        "minimalist jewelry",
        "vintage jewelry",
        "statement necklace",
    ],
    "metal_trends": [
        "rose gold jewelry",
        "yellow gold comeback",
        "platinum vs white gold",
        "mixed metal jewelry",
    ],
    "gemstone_trends": [
        "lab grown diamond",
        "colored gemstone jewelry",
        "moissanite engagement ring",
        "sustainable gemstones",
    ],
    "market_signals": [
        "jewelry price surge",
        "gold price impact",
        "luxury jewelry market",
        "jewelry brand acquisition",
    ],
}


def get_state() -> SignalState:
    return SignalState()


def get_registry() -> SignalRegistry:
    return SignalRegistry()


def seed_jewelry_targets() -> int:
    registry = get_registry()
    count = 0
    for prefix, queries in _JEWELRY_QUERIES.items():
        target = MonitoredTarget(
            handle=f"vivify_{prefix}",
            platform="reddit",
            queries=queries,
            cadence="daily",
            alert_threshold=0.6,
            enabled=True,
        )
        registry.add(target)
        count += 1
    return count


def list_targets() -> list[dict]:
    registry = get_registry()
    return [t.model_dump() for t in registry.list_all(enabled_only=False)]


def add_signal(handle: str, platform: str, text: str, topics: list[str]) -> dict:
    state = get_state()
    record = SignalRecord(
        target_id=f"{handle}@{platform}",
        handle=handle,
        platform=platform,
        text=text,
        topics=topics,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    state.store(record)
    return record.model_dump()


def query_signals(
    handle: str = "",
    platform: str = "",
    since: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    state = get_state()
    registry = get_registry()
    targets = registry.list_all(enabled_only=False)
    all_records: list[dict] = []
    for t in targets:
        if handle and t.handle != handle:
            continue
        if platform and t.platform != platform:
            continue
        records = state.query(t.handle, t.platform, since=since, limit=limit)
        all_records.extend(r.model_dump() for r in records)
    all_records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return all_records[:limit]


def get_trends_summary() -> dict:
    state = get_state()
    registry = get_registry()
    targets = registry.list_all()
    all_signals = []
    now = datetime.now(timezone.utc)

    for t in targets:
        records = state.query(t.handle, t.platform, limit=50)
        all_signals.extend(records)

    metals = {"ouro": 0, "prata": 0, "platina": 0, "rose_gold": 0}
    gemstones = {"diamante": 0, "esmeralda": 0, "safira": 0, "rubi": 0, "moissanite": 0}
    styles = {"minimalist": 0, "vintage": 0, "modern": 0, "custom": 0}

    for s in all_signals:
        text_lower = s.text.lower()
        for keyword in metals:
            if keyword in text_lower:
                metals[keyword] += 1
        for keyword in gemstones:
            if keyword in text_lower:
                gemstones[keyword] += 1
        for keyword in styles:
            if keyword in text_lower:
                styles[keyword] += 1

    return {
        "total_signals": len(all_signals),
        "total_targets": len(targets),
        "metal_mentions": metals,
        "gemstone_mentions": gemstones,
        "style_mentions": styles,
        "last_updated": now.isoformat(),
    }


def detect_anomalies(target_id: str = "") -> list[dict]:
    state = get_state()
    enricher = SignalEnricher()
    detector = AnomalyDetector(state=state)

    reports = []
    targets = get_registry().list_all()
    for t in targets:
        if target_id and t.target_id != target_id:
            continue
        records = state.query(t.handle, t.platform, limit=100)
        if not records:
            continue
        enriched = enricher.enrich_batch(records)
        report = detector.detect(t.target_id, enriched)
        reports.append(report.to_dict())
    return reports


def get_alerts(limit: int = 50) -> list[dict]:
    manager = AlertManager(channels=[FileLogChannel()])
    history = manager.history(limit=limit)
    return [a.to_dict() for a in history]
