#!/usr/bin/env python3
"""
Seed Vivify with demo data: jewels, certificates, trends signals.

Usage:
    python -m vivify.cli.seed_demo --api http://localhost:3334
"""

import json
import sys
import time

import httpx

API_URL = "http://localhost:3334"

DEMO_JEWELS = [
    {"name": "Anel de Noivado Solitaire", "metal": "ouro_18k", "gemstones": ["diamante"], "weight_grams": 4.5, "origin": "Brasil"},
    {"name": "Colar de Pérolas Imperial", "metal": "prata_925", "gemstones": ["perola"], "weight_grams": 18.2, "origin": "Japão"},
    {"name": "Brinco de Safira Celestial", "metal": "platina", "gemstones": ["safira", "diamante"], "weight_grams": 3.8, "origin": "Sri Lanka"},
    {"name": "Pulseira Ouro Rosé", "metal": "ouro_18k", "gemstones": ["rubi"], "weight_grams": 12.0, "origin": "Brasil"},
    {"name": "Anel Esmeralda Real", "metal": "ouro_24k", "gemstones": ["esmeralda", "diamante"], "weight_grams": 8.5, "origin": "Colômbia"},
    {"name": "Colar de Diamantes Aurora", "metal": "rodio", "gemstones": ["diamante", "diamante", "diamante"], "weight_grams": 22.0, "origin": "África do Sul"},
    {"name": "Anel Ametista Violeta", "metal": "prata_925", "gemstones": ["ametista"], "weight_grams": 6.3, "origin": "Brasil"},
    {"name": "Broche de Turmalina", "metal": "ouro_18k", "gemstones": ["turmalina"], "weight_grams": 9.0, "origin": "Brasil"},
    {"name": "Conjunto Noivado Clássico", "metal": "platina", "gemstones": ["diamante", "safira"], "weight_grams": 11.5, "origin": "Bélgica"},
    {"name": "Tornozeleira Verão", "metal": "ouro_18k", "gemstones": ["citrino", "topazio"], "weight_grams": 7.2, "origin": "Brasil"},
]

DEMO_TREND_SIGNALS = [
    ("Ouro rosé domina anéis de noivado em 2026", "ouro rosé, anel noivado, tendência"),
    ("Diamantes lab-grown ganham mercado de luxo", "diamante, laboratório, sustentável"),
    ("Platina volta com força em joias masculinas", "platina, joias masculinas, tendência"),
    ("Esmeralda colombiana tem alta de 40% no ano", "esmeralda, colômbia, preço"),
    ("Joalheiros adotam design minimalista escandinavo", "minimalista, design, escandinavo"),
    ("Ouro 24K bate recorde de demanda no oriente", "ouro 24k, demanda, oriente"),
    ("Ruby pink é a cor do ano em gemstones", "rubi, pink, cor do ano"),
    ("Mix de metais: ouro + prata + platina na mesma peça", "mix metais, tendência, design"),
]

DEMO_TARGETS = [
    "vivify_design_trends",
    "vivify_metal_trends",
    "vivify_gemstone_trends",
    "vivify_market_signals",
]


def seed_jewels(api_url: str) -> list[str]:
    ids = []
    print("  Creating demo jewels...")
    for j in DEMO_JEWELS:
        resp = httpx.post(f"{api_url}/jewels", json=j, timeout=10)
        if resp.status_code == 201:
            jewel_id = resp.json()["id"]
            ids.append(jewel_id)
            print(f"    ✓ {j['name']} ({jewel_id[:8]}...)")
        else:
            print(f"    ✗ {j['name']}: {resp.status_code}")
        time.sleep(0.1)
    return ids


def issue_certificates(api_url: str, jewel_ids: list[str]):
    print("  Issuing certificates...")
    for jid in jewel_ids:
        try:
            resp = httpx.post(f"{api_url}/certificates/{jid}", timeout=10)
            if resp.status_code == 200:
                print(f"    ✓ Certificate issued for {jid[:8]}...")
            elif resp.status_code == 409:
                print(f"    - Certificate already exists for {jid[:8]}...")
            else:
                print(f"    ✗ {resp.status_code}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
        time.sleep(0.1)


def seed_trends(api_url: str):
    print("  Seeding trend targets...")
    try:
        resp = httpx.post(f"{api_url}/trends/seed", timeout=10)
        if resp.status_code == 200:
            print(f"    ✓ {resp.json()['seeded']} targets seeded")
        else:
            print(f"    ✗ {resp.status_code}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    print("  Inserting trend signals...")
    for handle in DEMO_TARGETS:
        for text, topics in DEMO_TREND_SIGNALS:
            try:
                httpx.post(
                    f"{api_url}/trends/signals",
                    params={"handle": handle, "platform": "reddit", "text": text, "topics": topics},
                    timeout=10,
                )
            except Exception:
                pass
    print(f"    ✓ {len(DEMO_TREND_SIGNALS) * len(DEMO_TARGETS)} signals inserted")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed Vivify with demo data")
    parser.add_argument("--api", default=API_URL, help=f"Vivify API URL (default: {API_URL})")
    args = parser.parse_args()

    print("🌱 Seeding Vivify demo data...")
    print(f"  API: {args.api}\n")

    ids = seed_jewels(args.api)
    if ids:
        issue_certificates(args.api, ids)
    seed_trends(args.api)

    print(f"\n✅ Demo data seeded!")
    print(f"   {len(ids)} jewels, {len(ids)} certificates, {len(DEMO_TREND_SIGNALS) * len(DEMO_TARGETS)} trend signals")
    print(f"\n📋 Access the demo:")
    print(f"   Catalog:  http://localhost:3333/vivify")
    print(f"   Verify:   http://localhost:3333/vivify/verify/{ids[0][:8]}...")
    print(f"   Simulate: http://localhost:3333/vivify/simulate")
    print(f"   Trends:   http://localhost:3333/vivify/trends")


if __name__ == "__main__":
    main()
