"""SQLite persistence used by both the collector and Streamlit page."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import IntelligenceItem, RunStats


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _canonical_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
    )


def item_fingerprint(item: IntelligenceItem) -> str:
    identity = item.doi.lower().strip() or _canonical_url(item.url)
    if not identity:
        identity = f"{item.source_name.lower()}|{item.title.lower().strip()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize(db_path: Path | str) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS intelligence_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                fetched INTEGER NOT NULL DEFAULT 0,
                candidates INTEGER NOT NULL DEFAULT 0,
                new_items INTEGER NOT NULL DEFAULT 0,
                summarized INTEGER NOT NULL DEFAULT 0,
                metadata_only INTEGER NOT NULL DEFAULT 0,
                errors INTEGER NOT NULL DEFAULT 0,
                error_message TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS intelligence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                doi TEXT NOT NULL DEFAULT '',
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                published_at TEXT NOT NULL DEFAULT '',
                authors TEXT NOT NULL DEFAULT '',
                abstract TEXT NOT NULL DEFAULT '',
                snippet TEXT NOT NULL DEFAULT '',
                retrieved_at TEXT NOT NULL,
                rule_score INTEGER NOT NULL DEFAULT 0,
                matched_terms TEXT NOT NULL DEFAULT '[]',
                relevant INTEGER,
                model_score INTEGER,
                summary TEXT NOT NULL DEFAULT '',
                why_it_matters TEXT NOT NULL DEFAULT '',
                technologies TEXT NOT NULL DEFAULT '[]',
                topics TEXT NOT NULL DEFAULT '[]',
                tea_category TEXT NOT NULL DEFAULT 'Background Industry News',
                tea_parameters TEXT NOT NULL DEFAULT '[]',
                numerical_evidence TEXT NOT NULL DEFAULT '[]',
                review_recommended INTEGER NOT NULL DEFAULT 0,
                summary_basis TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                processing_status TEXT NOT NULL DEFAULT 'pending',
                processing_error TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_intelligence_published
                ON intelligence_items(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_intelligence_type
                ON intelligence_items(source_type);
            """
        )
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(intelligence_items)")
        }
        migrations = {
            "tea_category": "TEXT NOT NULL DEFAULT 'Background Industry News'",
            "tea_parameters": "TEXT NOT NULL DEFAULT '[]'",
            "numerical_evidence": "TEXT NOT NULL DEFAULT '[]'",
            "review_recommended": "INTEGER NOT NULL DEFAULT 0",
        }
        for column, declaration in migrations.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE intelligence_items ADD COLUMN {column} {declaration}"
                )


def start_run(db_path: Path | str) -> int:
    initialize(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO intelligence_runs(started_at, status) VALUES (?, 'running')",
            (_utc_now(),),
        )
        return int(cursor.lastrowid)


def finish_run(db_path: Path | str, stats: RunStats, status: str, error_message: str = "") -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE intelligence_runs
            SET completed_at=?, status=?, fetched=?, candidates=?, new_items=?,
                summarized=?, metadata_only=?, errors=?, error_message=?
            WHERE id=?
            """,
            (
                _utc_now(), status, stats.fetched, stats.candidates, stats.new_items,
                stats.summarized, stats.metadata_only, stats.errors, error_message, stats.run_id,
            ),
        )


def insert_item(db_path: Path | str, item: IntelligenceItem) -> tuple[int, bool]:
    initialize(db_path)
    fingerprint = item_fingerprint(item)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO intelligence_items(
                fingerprint, title, url, doi, source_name, source_type,
                published_at, authors, abstract, snippet, retrieved_at,
                rule_score, matched_terms, summary_basis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fingerprint, item.title, item.url, item.doi, item.source_name,
                item.source_type, item.published_at, item.authors, item.abstract,
                item.snippet, _utc_now(), item.rule_score,
                json.dumps(item.matched_terms), item.summary_basis,
            ),
        )
        inserted = cursor.rowcount == 1
        row = connection.execute(
            "SELECT id FROM intelligence_items WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        return int(row["id"]), inserted


def item_processing_status(db_path: Path | str, item_id: int) -> str:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT processing_status FROM intelligence_items WHERE id=?", (item_id,)
        ).fetchone()
        return str(row["processing_status"]) if row else ""


def update_analysis(db_path: Path | str, item_id: int, result: dict, model_name: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE intelligence_items
            SET relevant=?, model_score=?, summary=?, why_it_matters=?,
                technologies=?, topics=?, tea_category=?, tea_parameters=?,
                numerical_evidence=?, review_recommended=?, model_name=?,
                processing_status='summarized',
                processing_error=''
            WHERE id=?
            """,
            (
                int(bool(result.get("relevant"))), int(result.get("relevance_score", 0)),
                str(result.get("summary", "")).strip(),
                str(result.get("why_it_matters", "")).strip(),
                json.dumps(result.get("technologies", [])),
                json.dumps(result.get("topics", [])),
                str(result.get("tea_category", "Background Industry News")),
                json.dumps(result.get("tea_parameters", [])),
                json.dumps(result.get("numerical_evidence", [])),
                int(bool(result.get("review_recommended", False))),
                model_name, item_id,
            ),
        )


def mark_metadata_only(db_path: Path | str, item_id: int) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE intelligence_items
            SET relevant=1, tea_category='Background Industry News',
                processing_status='metadata_only'
            WHERE id=?
            """,
            (item_id,),
        )


def mark_error(db_path: Path | str, item_id: int, message: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE intelligence_items
            SET processing_status='error', processing_error=?
            WHERE id=?
            """,
            (message[:1000], item_id),
        )


def latest_run(db_path: Path | str):
    initialize(db_path)
    with connect(db_path) as connection:
        return connection.execute(
            "SELECT * FROM intelligence_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()


def list_items(
    db_path: Path | str,
    *,
    source_type: str = "All",
    tea_category: str = "All",
    search: str = "",
    days: int = 30,
    include_rejected: bool = False,
    limit: int = 200,
):
    initialize(db_path)
    clauses = ["datetime(COALESCE(NULLIF(published_at, ''), retrieved_at)) >= datetime('now', ?)"]
    params: list[object] = [f"-{int(days)} days"]
    if source_type != "All":
        clauses.append("source_type = ?")
        params.append(source_type)
    if tea_category != "All":
        clauses.append("tea_category = ?")
        params.append(tea_category)
    if search.strip():
        clauses.append("(title LIKE ? OR abstract LIKE ? OR snippet LIKE ? OR matched_terms LIKE ?)")
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern, pattern, pattern])
    if not include_rejected:
        clauses.append("COALESCE(relevant, 1) = 1")
    params.append(int(limit))
    query = f"""
        SELECT * FROM intelligence_items
        WHERE {' AND '.join(clauses)}
        ORDER BY datetime(COALESCE(NULLIF(published_at, ''), retrieved_at)) DESC, id DESC
        LIMIT ?
    """
    with connect(db_path) as connection:
        return connection.execute(query, params).fetchall()
