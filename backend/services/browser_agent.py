"""Browser automation via browser-use + SOC Gateway.

Delegates to storyforge-studio engine.scraper.browser_agent.
Vivify-specific: logs runs to hashchain, jewelry-specific scraping prompts.
"""
import logging

from engine.scraper.browser_agent import BrowserAutomationService as _BaseBrowserAgent
from ..storage.hashchain import append_jewel_entry

logger = logging.getLogger("vivify.browser_agent")


class BrowserAutomationService(_BaseBrowserAgent):
    async def _run_agent(self, task: str, max_steps: int = 30) -> str:
        result = await super()._run_agent(task, max_steps)

        append_jewel_entry(
            event_type="vivify.browser_agent.run",
            jewel_id="browser_agent_session",
            metadata={
                "task_preview": task[:120],
                "result_length": len(result),
                "steps": max_steps,
            },
        )
        return result

    async def extract_catalog(self, url: str) -> list[dict]:
        task = f"""
1. Acesse o site: {url}
2. Encontre o catálogo de produtos (joias). Navegue por todas as páginas de listagem.
3. Para CADA produto, extraia: nome, preço (apenas números), metal, lista de pedras, descrição curta, URL da imagem principal, SKU.
4. Retorne APENAS um array JSON válido. NÃO coloque texto antes ou depois.
   Exemplo: [{{"name":"Anel Ouro","price":"1500.00","metal":"ouro_18k","gemstones":["diamante"],"description":"...","image_url":"...","sku":"REF-001"}}]
5. Se houver mais de 20 produtos, colete todos.
"""
        result = await self._run_agent(task, max_steps=50)
        return self._parse_json(result) or []
