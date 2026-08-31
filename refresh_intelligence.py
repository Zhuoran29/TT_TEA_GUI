"""Command-line entry point for Task Scheduler or a server cron job."""

from __future__ import annotations

import argparse

from intelligence import IntelligenceSettings, refresh_intelligence


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh the water intelligence database.")
    parser.add_argument("--no-ai", action="store_true", help="Collect without calling Ollama.")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=("crossref", "gdelt", "rss"),
        default=("crossref", "gdelt", "rss"),
    )
    args = parser.parse_args()
    settings = IntelligenceSettings()
    stats = refresh_intelligence(settings, use_ai=not args.no_ai, sources=args.sources)
    print(
        f"run={stats.run_id} fetched={stats.fetched} candidates={stats.candidates} "
        f"new={stats.new_items} summarized={stats.summarized} "
        f"metadata_only={stats.metadata_only} errors={stats.errors}"
    )


if __name__ == "__main__":
    main()
