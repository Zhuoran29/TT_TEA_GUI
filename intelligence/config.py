"""Configuration for the water intelligence collector."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class IntelligenceSettings:
    """Runtime settings, with environment-variable overrides for deployment."""

    db_path: Path = Path(
        os.getenv(
            "INTELLIGENCE_DB_PATH",
            PROJECT_ROOT / "data" / "intelligence" / "intelligence.db",
        )
    )
    rss_config_path: Path = Path(
        os.getenv(
            "INTELLIGENCE_RSS_CONFIG",
            PROJECT_ROOT / "data" / "intelligence" / "rss_sources.json",
        )
    )
    ollama_url: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct")
    crossref_mailto: str = os.getenv("CROSSREF_MAILTO", "")
    lookback_days: int = _env_int("INTELLIGENCE_LOOKBACK_DAYS", 3)
    max_items_per_run: int = _env_int("INTELLIGENCE_MAX_ITEMS", 40)
    min_rule_score: int = _env_int("INTELLIGENCE_MIN_RULE_SCORE", 4)
    request_timeout: int = _env_int("INTELLIGENCE_REQUEST_TIMEOUT", 45)
    ollama_timeout: int = _env_int("OLLAMA_TIMEOUT", 180)

