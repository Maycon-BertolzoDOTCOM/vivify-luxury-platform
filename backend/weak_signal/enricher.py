"""Signal enricher — fetches market context via Odysseus intelligence channel + local sentiment."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from .schemas import SignalRecord

logger = logging.getLogger("vivify.weak_signal.enricher")

ODYSSEUS_URL = os.getenv("ODYSSEUS_URL", "http://localhost:8080")
ODYSSEUS_TIMEOUT = float(os.getenv("ODYSSEUS_TIMEOUT", "3.0"))


_SENTIMENT_KEYWORDS: dict[str, float] = {
    "bom": 0.3, "ótimo": 0.5, "excelente": 0.6, "lindo": 0.4, "maravilhoso": 0.6,
    "amo": 0.5, "amei": 0.6, "perfeito": 0.5, "qualidade": 0.3, "luxo": 0.2,
    "caro": -0.2, "ruim": -0.4, "péssimo": -0.6, "horrível": -0.7, "falso": -0.5,
    "golpe": -0.6, "enganou": -0.5, "arrepend": -0.4, "quebrou": -0.5,
    "manchou": -0.3, "desbotou": -0.3,
}

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "design": ["design", "estilo", "modelo", "formato", "tendência", "moderno", "clássico"],
    "metal": ["ouro", "prata", "platina", "paládio", "rose gold", "ouro branco", "ouro amarelo"],
    "gemstone": ["diamante", "esmeralda", "safira", "rubi", "moissanite", "zircônia", "opala"],
    "mercado": ["preço", "valor", "investimento", "lucro", "venda", "compra", "mercado"],
    "sustentabilidade": ["sustentável", "reciclado", "ético", "lab grown", "artesanal", "fair trade"],
    "personalização": ["personalizado", "sob medida", "customizado", "exclusivo", "único"],
}


def _compute_sentiment(text: str) -> dict[str, Any]:
    text_lower = text.lower()
    score = 0.0
    matches = 0
    for kw, val in _SENTIMENT_KEYWORDS.items():
        if kw in text_lower:
            score += val
            matches += 1
    if matches > 0:
        score /= matches
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    return {"score": round(score, 3), "label": label}


def _extract_topics(text: str) -> list[str]:
    text_lower = text.lower()
    found = set()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.add(topic)
    return sorted(found)


async def _fetch_odysseus_intelligence(signal: SignalRecord) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=ODYSSEUS_TIMEOUT) as client:
            resp = await client.post(
                f"{ODYSSEUS_URL}/v1/omnichannel/generate",
                json={
                    "channel": "intelligence",
                    "vertical": "jewelry",
                    "payload": {
                        "sources": ["shadowfeed"],
                        "query": signal.text[:500],
                        "limit": 3,
                    },
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {})
    except Exception as e:
        logger.debug("Odysseus unavailable: %s", e)
    return {}


class SignalEnricher:
    def __init__(self, enable_odysseus: bool = True):
        self.enable_odysseus = enable_odysseus
        self._context_cache: dict[str, Any] = {
            "enriched_at": datetime.now(timezone.utc).isoformat(),
            "market_data": [],
        }

    async def enrich_batch_async(self, records: list[SignalRecord]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for rec in records:
            entry = rec.model_dump()
            entry["sentiment"] = _compute_sentiment(rec.text)
            entry["detected_topics"] = _extract_topics(rec.text)

            if self.enable_odysseus and not self._context_cache.get("market_data"):
                ctx = await _fetch_odysseus_intelligence(rec)
                if ctx:
                    self._context_cache["market_data"] = ctx.get("events", [])
                    self._context_cache["trends"] = ctx.get("trends", [])

            enriched.append(entry)
        return enriched

    def enrich_batch(self, records: list[Any]) -> list[Any]:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(self.enrich_batch_async(records))
            finally:
                loop.close()
            return result
        except Exception as e:
            logger.warning("Enrichment failed, falling back to pass-through: %s", e)
            return records

    def get_context(self) -> dict[str, Any]:
        return dict(self._context_cache)
