"""HTTP scraper for competitor price intelligence.

Delegates to storyforge-studio engine.scraper.http_scraper.
Vivify-specific: logs scans to hashchain.
"""
import logging

from engine.scraper.http_scraper import HttpScraperService as _BaseScraper
from ..storage.hashchain import append_jewel_entry

logger = logging.getLogger("vivify.http_scraper")


class HttpScraperService(_BaseScraper):
    async def monitor_competitor(self, url: str) -> dict:
        html = await self.fetch_page(url)
        if not html:
            append_jewel_entry(
                event_type="vivify.http_scraper.failed",
                jewel_id="http_scraper",
                metadata={"url": url, "error": "fetch_failed"},
            )
            return {"competitor": url, "products": []}

        products = await self.scrape_products(url)
        products_list = products.get("products", [])

        logger.info("Scraped %d products from %s", len(products_list), url)

        append_jewel_entry(
            event_type="vivify.http_scraper.scan",
            jewel_id="http_scraper",
            metadata={"url": url, "products_found": len(products_list)},
        )
        return {"competitor": url, "products": products_list}

    async def extract_catalog(self, url: str) -> list[dict]:
        result = await self.monitor_competitor(url)
        return result.get("products", [])
