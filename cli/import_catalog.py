#!/usr/bin/env python3
"""
Import jewelry catalog from CSV or JSON into Vivify.

Usage:
    python -m vivify.cli.import_catalog catalog.csv --api http://localhost:3334
    python -m vivify.cli.import_catalog catalog.json --api http://localhost:3334
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

API_URL = "http://localhost:3334"


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_json(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "jewels" in data:
        return data["jewels"]
    raise ValueError("JSON must be a list of jewels or {jewels: [...]}")


def normalize(row: dict) -> dict:
    return {
        "name": row.get("name", row.get("Name", row.get("nome", "Unnamed"))),
        "metal": row.get("metal", row.get("Metal", row.get("metais", "ouro_18k"))),
        "gemstones": _parse_list(row, "gemstones", "Gemstones", "pedras"),
        "weight_grams": float(row.get("weight_grams", row.get("Weight", row.get("peso", 0)))),
        "origin": row.get("origin", row.get("Origin", row.get("origem", ""))) or None,
        "status": "disponivel",
    }


def _parse_list(row: dict, *keys: str) -> list[str]:
    for k in keys:
        val = row.get(k)
        if val:
            if isinstance(val, str):
                return [s.strip() for s in val.split(",") if s.strip()]
            if isinstance(val, list):
                return val
    return []


def import_jewels(items: list[dict], api_url: str = API_URL, delay: float = 0.2) -> dict:
    results = {"ok": 0, "fail": 0, "errors": []}
    for item in items:
        try:
            normalized = normalize(item)
            resp = httpx.post(f"{api_url}/jewels", json=normalized, timeout=10)
            if resp.status_code == 201:
                results["ok"] += 1
                print(f"  ✓ {normalized['name']}", flush=True)
            else:
                results["fail"] += 1
                err = f"{normalized['name']}: HTTP {resp.status_code} - {resp.text}"
                results["errors"].append(err)
                print(f"  ✗ {err}", flush=True)
        except Exception as e:
            results["fail"] += 1
            err = f"Error importing: {e}"
            results["errors"].append(err)
            print(f"  ✗ {err}", flush=True)
        time.sleep(delay)
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import jewelry catalog into Vivify")
    parser.add_argument("file", help="CSV or JSON file")
    parser.add_argument("--api", default=API_URL, help=f"Vivify API URL (default: {API_URL})")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    if path.suffix.lower() == ".csv":
        items = load_csv(str(path))
    elif path.suffix.lower() == ".json":
        items = load_json(str(path))
    else:
        print("❌ Unsupported format. Use .csv or .json")
        sys.exit(1)

    print(f"📦 Importing {len(items)} jewels from {path.name}...")
    results = import_jewels(items, args.api)
    print(f"\n✅ {results['ok']} imported, ❌ {results['fail']} failed")
    if results["errors"]:
        for err in results["errors"][:5]:
            print(f"  - {err}")
    sys.exit(0 if results["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
