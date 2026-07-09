from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ..services.trends import (
    seed_jewelry_targets,
    list_targets,
    add_signal,
    query_signals,
    get_trends_summary,
    get_enriched_trends_summary,
    detect_anomalies,
    get_alerts,
    get_market_context,
)
from ..services.llm import SOCLLMService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.post("/seed")
def seed_targets():
    count = seed_jewelry_targets()
    return {"seeded": count, "status": "ok"}


@router.get("/targets")
def targets():
    return {"targets": list_targets(), "total": len(list_targets())}


@router.post("/signals")
def submit_signal(
    handle: str = Query("vivify_design_trends"),
    platform: str = Query("reddit"),
    text: str = Query(...),
    topics: str = Query(""),
):
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    result = add_signal(handle, platform, text, topic_list)
    return result


@router.get("/signals")
def list_signals(
    handle: str = Query(""),
    platform: str = Query(""),
    since: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    signals = query_signals(handle=handle, platform=platform, since=since, limit=limit)
    return {"signals": signals, "total": len(signals)}


@router.get("/summary")
def summary():
    return get_trends_summary()


@router.get("/enriched-summary")
def enriched_summary():
    return get_enriched_trends_summary()


@router.get("/anomalies")
def anomalies(target_id: Optional[str] = Query("")):
    return {"anomalies": detect_anomalies(target_id or "")}


@router.get("/alerts")
def alerts(
    limit: int = Query(50, ge=1, le=200),
    target_id: str = Query(""),
):
    return {"alerts": get_alerts(limit=limit, target_id=target_id)}


@router.get("/market-context")
async def market_context():
    data = await get_market_context()
    return data


_llm = SOCLLMService()


@router.post("/narrative")
async def trend_narrative():
    summary = get_enriched_trends_summary() if get_trends_summary().get("total_signals", 0) > 0 else get_trends_summary()
    narrative = await _llm.generate_trend_narrative(summary)
    return {"narrative": narrative, "source": "soc_gateway"}
