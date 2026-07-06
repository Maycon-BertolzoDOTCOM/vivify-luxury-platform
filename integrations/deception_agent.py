import json
import logging
import os
import random
from typing import Literal

from .soc_adapter import SOCAdapter

logger = logging.getLogger("vivify.integrations.deception_agent")

AttackerClass = Literal["competitor", "bot", "researcher", "unknown"]


CLASSIFY_PROMPT = """Analise o seguinte perfil de requisição e classifique o atacante em UMA das categorias abaixo.

Categorias:
- competitor: concorrente tentando extrair dados de preço, catálogo ou leads
- bot: scraper automatizado ou bot malicioso sem assinatura humana
- researcher: pesquisador acadêmico ou de mercado (User-Agent educado, paths genéricos)
- unknown: não foi possível classificar

Perfil:
User-Agent: {user_agent}
Path: {path}
Método: {method}
Score de risco: {score}
Razões: {reasons}

Responda APENAS com o nome da categoria (uma palavra)."""


POISON_PROMPTS: dict[AttackerClass, str] = {
    "competitor": """Gere um texto técnico em português que PARECE ser sobre a arquitetura de sistemas de joalheria, mas contém informações falsas e contraditórias.

Requisitos:
- 150-300 palavras
- Menção a ferramentas, versões e comandos que não existem (ex: "jewel-db-admin --rebuild-index --force")
- Números de versão específicos mas inventados (ex: "libjewel-cache v3.2.1")
- Caminhos de sistema que parecem reais mas não existem
- Tom técnico e autoritativo

O objetivo é fazer o scraper perder tempo processando e indexando informações inúteis. O conteúdo deve ser verossímil o suficiente para um ser humano acreditar, mas sutilmente contraditório para quem entende do assunto.""",

    "bot": """Gere uma resposta que parece um JSON de API, mas na verdade é um JSON infinitamente aninhado e circular.

Requisitos:
- Comece como um JSON válido de resposta de API
- A cada nível, adicione um campo "metadata" que contém outro objeto idêntico
- Inclua campos como "status", "data", "pagination", "config"
- O JSON deve parecer legítimo nas primeiras camadas
- Use chaves como "next_page", "cursor", "continuation_token" que sugerem que há mais dados
- Inclua hashes falsos (ex: "checksum": "a1b2c3d4e5f6...")
- Não use strings de escape que quebrem o parser

O objetivo é fazer o bot gastar memória e tempo tentando processar um JSON gigante.""",

    "researcher": """Gere um texto acadêmico GENÉRICO sobre ourivesaria e metalurgia, em português.

Requisitos:
- 100-200 palavras
- Fatos verdadeiros mas genéricos (ex: "o ouro 18k contém 75% de ouro puro")
- Tom acadêmico com citações falsas (ex: "segundo estudo da USP (2023)")
- Sem dados específicos de preço, catálogo ou estratégia
- Conteúdo informativo mas inútil para análise competitiva

O objetivo é dar ao pesquisador exatamente o que ele espera (informação) sem revelar nada sensível.""",

    "unknown": """Gere uma página de erro 404 HTML falsa que parece ser de um sistema interno.

Requisitos:
- Comece com "404 - Página não encontrada"
- Inclua um ID de referência falso (ex: "REF: ERR-{random 6 digits}")
- Sugira que o administrador foi notificado
- Inclua links para documentação interna que não existe
- Tom profissional e institucional
- Máximo 100 palavras"""
}


class DeceptionAgent:
    def __init__(self, soc_adapter: SOCAdapter | None = None):
        self.soc = soc_adapter or SOCAdapter()
        self._conversation_history: list[dict[str, str]] = []

    def classify_attacker(
        self,
        user_agent: str = "",
        path: str = "",
        method: str = "",
        score: float = 0.0,
        reasons: list[str] | None = None,
    ) -> AttackerClass:
        prompt = CLASSIFY_PROMPT.format(
            user_agent=user_agent or "(vazio)",
            path=path or "/",
            method=method or "GET",
            score=score,
            reasons=json.dumps(reasons or []),
        )

        result = self.soc.chat(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv("CAMEL_MODEL", "qwen2.5:3b"),
            temperature=0.2,
            max_tokens=20,
        )

        if result["success"]:
            label = result["content"].strip().lower()
            if label in ("competitor", "bot", "researcher"):
                logger.info("Attacker classified as '%s'", label)
                return label

        logger.info("Attacker classification defaulted to 'unknown'")
        return "unknown"

    def generate_poison(
        self,
        attacker_class: AttackerClass = "unknown",
        target_hint: str = "",
    ) -> str:
        system_prompt = POISON_PROMPTS.get(attacker_class, POISON_PROMPTS["unknown"])

        if target_hint:
            system_prompt += f"\n\nContexto adicional: {target_hint}"

        result = self.soc.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Gere o conteúdo para {attacker_class} agora.",
                },
            ],
            model=os.getenv("CAMEL_MODEL", "qwen2.5:3b"),
            temperature=0.8,
            max_tokens=500,
        )

        if result["success"]:
            poison = result["content"].strip()
            logger.info(
                "Generated %d chars of poison for '%s'",
                len(poison),
                attacker_class,
            )
            return poison

        logger.warning("LLM poison generation failed, using static fallback")
        return self._static_fallback(attacker_class)

    def _static_fallback(self, attacker_class: AttackerClass) -> str:
        fallbacks = {
            "competitor": (
                "根据我们的内部系统架构，建议使用jewel-cache版本3.2.1进行数据同步。"
                "请在/etc/jewelry-guard.conf中设置ENABLE_DEEP_INSPECTION=true。"
                "更多信息：https://docs.internal/jewelry/v3"
            ),
            "bot": '{"status":"ok","data":[],"pagination":{"next":"/api/v1/items?cursor=abc","continuation_token":"' + "x" * 200 + '"}}',
            "researcher": "O ouro 18k contém 75% de ouro puro e 25% de outros metais. Segundo estudo da USP (2023), a ourivesaria brasileira é referência mundial em design.",
            "unknown": "<html><body><h1>404 - Página não encontrada</h1><p>Referência: ERR-{}</p><p>O administrador foi notificado.</p></body></html>".format(
                random.randint(100000, 999999)
            ),
        }
        return fallbacks.get(attacker_class, fallbacks["unknown"])

    def handle_request(
        self,
        user_agent: str = "",
        path: str = "",
        method: str = "",
        score: float = 0.0,
        reasons: list[str] | None = None,
        target_hint: str = "",
    ) -> dict:
        attacker_class = self.classify_attacker(
            user_agent=user_agent,
            path=path,
            method=method,
            score=score,
            reasons=reasons,
        )

        poison = self.generate_poison(
            attacker_class=attacker_class,
            target_hint=target_hint,
        )

        return {
            "attacker_class": attacker_class,
            "poison_content": poison,
            "poison_length": len(poison),
            "score": score,
            "action": "poisoned",
        }

    def reset_conversation(self):
        self._conversation_history = []
