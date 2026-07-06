"""Vivify-specific job scheduling — competitor scans, trend analysis.

Uses storyforge-studio engine.scheduler for the cron backbone.
"""
import logging
from datetime import datetime, timezone

from engine.scheduler import register_job, start as _engine_start, stop as _engine_stop

from ..storage.db import fetchall, execute, fetchone
from ..services.trends import add_signal
from ..services.http_scraper import HttpScraperService

logger = logging.getLogger("vivify.scheduler")


async def scan_competitor(competitor_id: str, url: str, label: str) -> dict:
    scraper = HttpScraperService()
    try:
        data = await scraper.monitor_competitor(url)
        products = data.get("products", [])
        for p in products:
            add_signal(
                handle="vivify_competitor",
                platform="web",
                text=f"Concorrente {label}: {p.get('name', '?')} por {p.get('price', '?')}",
                topics=["competitor", "price", "monitoring", "automated"],
            )
        execute(
            "UPDATE monitored_competitors SET last_scan = ?, last_error = NULL, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), competitor_id),
        )
        logger.info("Competitor %s scanned: %d products", label, len(products))
        return {"success": True, "products": len(products)}
    except Exception as e:
        logger.warning("Competitor %s scan failed: %s", label, e)
        execute(
            "UPDATE monitored_competitors SET last_error = ?, updated_at = ? WHERE id = ?",
            (str(e)[:500], datetime.now(timezone.utc).isoformat(), competitor_id),
        )
        return {"success": False, "error": str(e)}


async def monitor_all_competitors():
    rows = fetchall("SELECT id, url, label FROM monitored_competitors WHERE active = 1")
    if not rows:
        logger.info("No active competitors to scan")
        return
    logger.info("Starting scan of %d competitors", len(rows))
    for row in rows:
        await scan_competitor(row["id"], row["url"], row["label"])


def start_scheduler():
    register_job(
        job_id="vivify_competitor_monitoring",
        fn=monitor_all_competitors,
        cron="0 8 * * 1",
        misfire_grace_time=3600,
    )
    _engine_start()


def stop_scheduler():
    _engine_stop()
