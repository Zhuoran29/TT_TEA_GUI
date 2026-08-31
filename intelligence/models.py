"""Data objects shared by source adapters, storage, and summarization."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntelligenceItem:
    title: str
    url: str
    source_name: str
    source_type: str
    published_at: str = ""
    doi: str = ""
    authors: str = ""
    abstract: str = ""
    snippet: str = ""
    rule_score: int = 0
    matched_terms: list[str] = field(default_factory=list)

    @property
    def summary_source(self) -> str:
        return self.abstract or self.snippet

    @property
    def summary_basis(self) -> str:
        if self.abstract:
            return "abstract"
        if self.snippet:
            return "public snippet"
        return "metadata only"


@dataclass
class RunStats:
    run_id: int
    fetched: int = 0
    candidates: int = 0
    new_items: int = 0
    summarized: int = 0
    metadata_only: int = 0
    errors: int = 0

