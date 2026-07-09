"""Trends service — weak signal detection for jewelry market intelligence."""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from ..weak_signal.schemas import MonitoredTarget, SignalRecord
from ..weak_signal.state import SignalState
from ..weak_signal.registry import SignalRegistry
from ..weak_signal.enricher import SignalEnricher
from ..weak_signal.anomaly import AnomalyDetector
from ..weak_signal.alerts import AlertManager, AlertRecord, FileLogChannel

logger = logging.getLogger("vivify.trends")

_SIGNAL_STATE = SignalState()
_SIGNAL_REGISTRY = SignalRegistry()

_ALERT_MANAGER = AlertManager(channels=[FileLogChannel()])
_ENRICHER = SignalEnricher(enable_odysseus=True)

ODYSSEUS_URL = os.getenv("ODYSSEUS_URL", "http://localhost:8080")
ODYSSEUS_TIMEOUT = float(os.getenv("ODYSSEUS_TIMEOUT", "5.0"))


def get_state() -> SignalState:
    return _SIGNAL_STATE


def get_registry() -> SignalRegistry:
    return _SIGNAL_REGISTRY


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


def get_enriched_trends_summary() -> dict:
    summary = get_trends_summary()
    context = _ENRICHER.get_context()
    if context.get("market_data"):
        summary["market_events"] = context["market_data"]
    if context.get("trends"):
        summary["market_trends"] = context["trends"]
    return summary


def detect_anomalies(target_id: str = "") -> list[dict]:
    state = get_state()
    enricher = SignalEnricher(enable_odysseus=False)
    detector = AnomalyDetector(state=state, std_multiplier=2.0)

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

        if report.anomaly_count > 0 and report.score >= getattr(t, "alert_threshold", 0.6):
            _ALERT_MANAGER.emit(
                target_id=t.target_id,
                message=f"Anomalia detectada: {report.anomaly_count} keyword(s) com z-score > {detector.std_multiplier} (score={report.score})",
                severity="high" if report.score > 0.8 else "medium",
            )

    return reports


def get_alerts(limit: int = 50, target_id: str = "") -> list[dict]:
    history = _ALERT_MANAGER.history(limit=limit, target_id=target_id)
    return [a.to_dict() for a in history]


async def get_market_context() -> dict:
    try:
        async with httpx.AsyncClient(timeout=ODYSSEUS_TIMEOUT) as client:
            resp = await client.post(
                f"{ODYSSEUS_URL}/v1/omnichannel/generate",
                json={
                    "channel": "intelligence",
                    "vertical": "jewelry",
                    "payload": {
                        "sources": ["shadowfeed", "predictive"],
                        "query": "jewelry market trends",
                        "limit": 10,
                    },
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {})
    except Exception as e:
        logger.debug("Odysseus market context unavailable: %s", e)
    return {}
