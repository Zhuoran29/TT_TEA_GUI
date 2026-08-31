"""Orchestrates retrieval, filtering, deduplication, and local summarization."""

from __future__ import annotations

from collections.abc import Iterable

from .config import IntelligenceSettings
from .db import (
    finish_run,
    insert_item,
    item_processing_status,
    mark_error,
    mark_metadata_only,
    start_run,
    update_analysis,
)
from .models import IntelligenceItem, RunStats
from .sources import fetch_crossref, fetch_gdelt, fetch_rss
from .summarizer import analyze_with_ollama


SOURCE_FETCHERS = {
    "crossref": fetch_crossref,
    "gdelt": fetch_gdelt,
    "rss": fetch_rss,
}


def _deduplicate(items: Iterable[IntelligenceItem]) -> list[IntelligenceItem]:
    seen: set[str] = set()
    result: list[IntelligenceItem] = []
    for item in sorted(items, key=lambda value: value.rule_score, reverse=True):
        key = (item.doi or item.url or f"{item.source_name}|{item.title}").lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def refresh_intelligence(
    settings: IntelligenceSettings | None = None,
    *,
    use_ai: bool = True,
    sources: Iterable[str] = ("crossref", "gdelt", "rss"),
) -> RunStats:
    settings = settings or IntelligenceSettings()
    stats = RunStats(run_id=start_run(settings.db_path))
    all_items: list[IntelligenceItem] = []
    source_errors: list[str] = []
    try:
        for source in sources:
            fetcher = SOURCE_FETCHERS.get(source)
            if fetcher is None:
                source_errors.append(f"Unknown source: {source}")
                continue
            try:
                all_items.extend(fetcher(settings))
            except Exception as exc:
                source_errors.append(f"{source}: {exc}")
                stats.errors += 1

        stats.fetched = len(all_items)
        candidates = [
            item for item in _deduplicate(all_items)
            if item.rule_score >= settings.min_rule_score
        ][: settings.max_items_per_run]
        stats.candidates = len(candidates)

        for item in candidates:
            item_id, inserted = insert_item(settings.db_path, item)
            stats.new_items += 1
            if not inserted:
                stats.new_items -= 1
                if not use_ai or item_processing_status(settings.db_path, item_id) not in {"pending", "error"}:
                    continue
            if not item.summary_source:
                if inserted:
                    mark_metadata_only(settings.db_path, item_id)
                    stats.metadata_only += 1
                continue
            if not use_ai:
                continue
            try:
                result = analyze_with_ollama(item, settings)
                update_analysis(settings.db_path, item_id, result, settings.ollama_model)
                stats.summarized += 1
            except Exception as exc:
                mark_error(settings.db_path, item_id, str(exc))
                stats.errors += 1

        status = "partial" if source_errors or stats.errors else "completed"
        finish_run(settings.db_path, stats, status, "; ".join(source_errors))
        return stats
    except Exception as exc:
        stats.errors += 1
        finish_run(settings.db_path, stats, "failed", str(exc))
        raise
