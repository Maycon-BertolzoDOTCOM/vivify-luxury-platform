"""Defense module — scraper detection + semantic poison generation.

Uses storyforge-studio engine.defense.scraper_detect for the core logic.
Vivify-specific: DB path, jewelry-themed poison templates.
"""
import importlib
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("vivify.defense")

DB_PATH = os.getenv("VIVIFY_DEFENSE_DB", str(Path(__file__).resolve().parent.parent.parent / "vivify_defense.db"))

# Patch the engine's DB path before importing its functions
os.environ["STORYFORGE_DEFENSE_DB"] = DB_PATH

from engine.defense.scraper_detect import (  # noqa: E402
    detect_scraper,
    generate_poison as _engine_poison,
    generate_poison_cloudflare,
    log_event,
    get_stats,
)


# Re-export with default DB override
def generate_poison(target_hint: str = "", lang: str = "zh") -> str:
    return _engine_poison(target_hint=target_hint, lang=lang)
