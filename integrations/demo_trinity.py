#!/usr/bin/env python3
"""
Demonstração da Trinity Ofensiva-Defensiva:
  defense.py (detecção) → DeceptionAgent (classificação + poison) → AuditBridge (hashchain)

Uso: python3 vivify/integrations/demo_trinity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from vivify.backend.services.defense import detect_scraper, generate_poison
from vivify.integrations.deception_agent import DeceptionAgent
from vivify.integrations.audit_bridge import AuditBridge


def simulate_scraper_ua(user_agent: str, path: str = "/", method: str = "GET", rate: int = 0):
    print(f"\n{'='*60}")
    print(f"Requisição: {method} {path}")
    print(f"User-Agent: {user_agent[:60]}...")
    print(f"Rate: {rate}/min")

    # Passo 1: SOC (defense.py) detecta o scraper
    result = detect_scraper(
        remote_ip="192.0.2.1",
        user_agent=user_agent,
        path=path,
        method=method,
        rate=rate,
    )
    print(f"\n🔍 defense.py detectou: score={result['score']}, is_scraper={result['is_scraper']}")
    print(f"   Razões: {result['reasons']}")

    if not result["is_scraper"]:
        print("   ✅ Tráfego legítimo — permitindo")
        return

    # Passo 2: CAMEL (DeceptionAgent) classifica o atacante e gera poison adaptativo
    agent = DeceptionAgent()
    response = agent.handle_request(
        user_agent=user_agent,
        path=path,
        method=method,
        score=result["score"],
        reasons=result["reasons"],
        target_hint=f"path={path}",
    )
    print(f"\n🐫 DeceptionAgent: classe={response['attacker_class']}, poison={response['poison_length']} chars")

    # Passo 3: SOC (AuditBridge) registra na hashchain
    bridge = AuditBridge()
    audit = bridge.log_action(
        action="adaptive_poison",
        target=path,
        agent=f"deception_agent/{response['attacker_class']}",
        metadata={
            "score": result["score"],
            "user_agent": user_agent[:100],
            "poison_length": response["poison_length"],
            "classification": response["attacker_class"],
        },
    )
    print(f"🔗 AuditBridge: hash={audit.get('hash', '?')[:16]}...")

    # Mostra amostra do poison
    poison_preview = response["poison_content"][:150]
    print(f"\n💉 Poison sample: {poison_preview}...")

    return response


def main():
    print("=" * 60)
    print("TRINITY OFENSIVA-DEFENSIVA — Demonstração")
    print("defense.py → DeceptionAgent → AuditBridge")
    print("=" * 60)

    cenarios = [
        ("Concorrente (PriceBot)", "Mozilla/5.0 (compatible; PriceBot/1.0)", "/api/jewels?limit=1000", 80),
        ("Bot Genérico (Scrapy)", "Scrapy/2.6 (+https://scrapy.org)", "/admin/config", 5),
        ("Pesquisador (Acadêmico)", "Mozilla/5.0 (compatible; AcademicBot/1.0)", "/research/materials", 2),
        ("Legítimo (Chrome)", "Mozilla/5.0 (Windows NT 10.0; Chrome/120.0)", "/", 3),
    ]

    for nome, ua, path, rate in cenarios:
        simulate_scraper_ua(ua, path, rate=rate)

    print(f"\n{'='*60}")
    print("✅ Trinity demonstrada com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
