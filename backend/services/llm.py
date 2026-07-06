"""Bridge para o SOC Gateway — LLM via SmartRouter com fallback.

Uses storyforge-studio engine.ai.llm as base, with Vivify-specific
jewelry prompts on top.
"""
import logging

from engine.ai.llm import LLMService
from ..config import SOC_GATEWAY_URL

logger = logging.getLogger("vivify.llm")

DESCRIPTION_TEMPLATES = {
    "default": "Jóia em {metal}, peça exclusiva com design artesanal. Peso: {weight}g.",
    "com_gemas": "Jóia em {metal} com {gemstones}, peso {weight}g. Edição limitada com certificado digital de proveniência imutável.",
}


class SOCLLMService(LLMService):
    def __init__(self):
        super().__init__(gateway_url=SOC_GATEWAY_URL)

    async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=500, tier="medium"):
        return await super().generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model="openrouter/auto",
            temperature=temperature,
            max_tokens=max_tokens,
            tier=tier,
        )

    async def describe_jewel(
        self, name: str, metal: str, gemstones: list[str], weight: float
    ) -> str:
        system = (
            "Você é um redator de luxo para joalheria de alto padrão. "
            "Suas descrições são sofisticadas, poéticas, destacam o brilho, "
            "a exclusividade e a arte da peça. Máximo 100 palavras. "
            "Responda em português do Brasil."
        )
        gem_part = f" com {' e '.join(gemstones)}" if gemstones else ""
        user = (
            f"Crie uma descrição de luxo para: {name}, "
            f"em {metal}{gem_part}, peso {weight}g."
        )
        result = await self.generate(prompt=user, system_prompt=system, temperature=0.8)
        if result["success"]:
            return result["content"]
        template_key = "com_gemas" if gemstones else "default"
        return DESCRIPTION_TEMPLATES[template_key].format(
            metal=metal, weight=weight, gemstones=" e ".join(gemstones)
        )

    async def generate_trend_narrative(self, summary_data: dict) -> str:
        system = (
            "Você é um analista de mercado especializado em joalheria. "
            "Gere um relatório conciso (3-5 frases) interpretando as tendências. "
            "Responda em português do Brasil."
        )
        user = f"Resuma estas tendências de joalheria: {summary_data}"
        result = await self.generate(
            prompt=user, system_prompt=system, temperature=0.7
        )
        if result["success"]:
            return result["content"]
        return (
            "Mercado joalheiro estável. "
            "Acompanhe os sinais fracos no dashboard de tendências para "
            "identificar movimentos emergentes."
        )
