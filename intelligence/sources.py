"""Adapters for public publication, news, and RSS sources."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import IntelligenceSettings
from .models import IntelligenceItem
from .scoring import relevance_score


SEARCH_QUERIES = (
    '"produced water" treatment',
    '"oilfield wastewater" treatment reuse',
    '"brackish water" treatment desalination',
    '"brackish groundwater" membrane desalination',
)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_markup(value: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(unescape(value or ""))
        return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    except Exception:
        return re.sub(r"<[^>]+>", " ", value or "").strip()


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "NMSU-Water-Intelligence/0.1"})
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _date_parts(message: dict) -> str:
    for key in ("published-print", "published-online", "published", "created"):
        parts = message.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            values = list(parts[0]) + [1, 1]
            try:
                return date(int(values[0]), int(values[1]), int(values[2])).isoformat()
            except (TypeError, ValueError):
                continue
    return ""


def fetch_crossref(settings: IntelligenceSettings) -> list[IntelligenceItem]:
    session = _session()
    start_date = (date.today() - timedelta(days=settings.lookback_days)).isoformat()
    found: list[IntelligenceItem] = []
    rows = max(10, min(30, settings.max_items_per_run))
    failures: list[str] = []
    for query in SEARCH_QUERIES:
        params = {
            "query.bibliographic": query.replace('"', ""),
            "filter": f"from-pub-date:{start_date},type:journal-article",
            "select": "DOI,title,author,abstract,URL,published,published-online,published-print,container-title",
            "sort": "relevance",
            "order": "desc",
            "rows": rows,
        }
        if settings.crossref_mailto:
            params["mailto"] = settings.crossref_mailto
        try:
            response = session.get(
                "https://api.crossref.org/works", params=params, timeout=settings.request_timeout
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            failures.append(f"{query}: {exc}")
            continue
        for message in response.json().get("message", {}).get("items", []):
            title = clean_markup(" ".join(message.get("title") or []))
            if not title:
                continue
            abstract = clean_markup(message.get("abstract", ""))
            journal = " ".join(message.get("container-title") or []) or "Crossref"
            authors = "; ".join(
                " ".join(filter(None, (author.get("given"), author.get("family"))))
                for author in message.get("author", [])
            )
            score, terms = relevance_score(f"{title} {abstract} {journal}")
            found.append(
                IntelligenceItem(
                    title=title,
                    url=message.get("URL", ""),
                    doi=message.get("DOI", ""),
                    source_name=journal,
                    source_type="Publication",
                    published_at=_date_parts(message),
                    authors=authors,
                    abstract=abstract,
                    rule_score=score,
                    matched_terms=terms,
                )
            )
    if not found and failures:
        raise RuntimeError("; ".join(failures))
    return found


def fetch_gdelt(settings: IntelligenceSettings) -> list[IntelligenceItem]:
    session = _session()
    query = (
        '(("produced water" OR "oilfield wastewater") AND (treatment OR reuse OR desalination)) '
        'OR (("brackish water" OR "brackish groundwater") AND (treatment OR desalination OR membrane))'
    )
    response = session.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "timespan": f"{max(1, min(settings.lookback_days, 7))}d",
            "maxrecords": max(25, min(settings.max_items_per_run * 2, 250)),
        },
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    found: list[IntelligenceItem] = []
    for article in response.json().get("articles", []):
        title = clean_markup(article.get("title", ""))
        if not title:
            continue
        score, terms = relevance_score(title)
        seen = str(article.get("seendate", ""))
        published = ""
        try:
            published = datetime.strptime(seen[:14], "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc
            ).isoformat(timespec="seconds")
        except ValueError:
            pass
        found.append(
            IntelligenceItem(
                title=title,
                url=article.get("url", ""),
                source_name=article.get("domain", "GDELT"),
                source_type="News",
                published_at=published,
                snippet=clean_markup(article.get("snippet", "")),
                rule_score=score,
                matched_terms=terms,
            )
        )
    return found


def _first_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in element.iter():
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name in names and child.text:
            return child.text.strip()
    return ""


def _entry_link(element: ET.Element) -> str:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1].lower() == "link":
            return child.attrib.get("href", "") or (child.text or "").strip()
    return ""


def _parse_feed_date(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat(timespec="seconds")
        except ValueError:
            return ""


def load_rss_sources(config_path: Path) -> list[dict]:
    if not config_path.exists():
        return []
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return [item for item in payload if item.get("name") and item.get("url")]


def fetch_rss(settings: IntelligenceSettings) -> list[IntelligenceItem]:
    session = _session()
    found: list[IntelligenceItem] = []
    for source in load_rss_sources(settings.rss_config_path):
        response = session.get(source["url"], timeout=settings.request_timeout)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        entries = [
            node for node in root.iter()
            if node.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}
        ]
        for entry in entries:
            title = clean_markup(_first_text(entry, ("title",)))
            summary = clean_markup(_first_text(entry, ("description", "summary", "content")))
            if not title:
                continue
            score, terms = relevance_score(f"{title} {summary}")
            found.append(
                IntelligenceItem(
                    title=title,
                    url=_entry_link(entry),
                    source_name=source["name"],
                    source_type=source.get("type", "Newsletter"),
                    published_at=_parse_feed_date(
                        _first_text(entry, ("pubdate", "published", "updated"))
                    ),
                    snippet=summary,
                    rule_score=score,
                    matched_terms=terms,
                )
            )
    return found
