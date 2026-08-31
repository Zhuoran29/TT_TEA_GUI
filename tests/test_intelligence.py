import json

from intelligence.config import IntelligenceSettings
from intelligence.db import insert_item, item_fingerprint, latest_run, list_items, update_analysis
from intelligence.models import IntelligenceItem
from intelligence.pipeline import refresh_intelligence
from intelligence.scoring import relevance_score
from intelligence.sources import clean_markup
from intelligence.summarizer import analyze_with_ollama


def test_relevance_score_prefers_domain_specific_phrases():
    score, terms = relevance_score(
        "Produced water treatment using reverse osmosis and beneficial reuse"
    )
    assert score >= 10
    assert "produced water" in terms
    assert "reverse osmosis" in terms


def test_clean_markup_removes_crossref_jats_tags():
    value = "<jats:p>Treatment reduced <jats:italic>salinity</jats:italic>.</jats:p>"
    assert clean_markup(value) == "Treatment reduced salinity ."


def test_fingerprint_ignores_tracking_parameters():
    first = IntelligenceItem("Title", "https://example.com/story?utm_source=x", "Source", "News")
    second = IntelligenceItem("Title", "https://example.com/story", "Source", "News")
    assert item_fingerprint(first) == item_fingerprint(second)


def test_database_insert_and_list(tmp_path):
    db_path = tmp_path / "intelligence.db"
    item = IntelligenceItem(
        title="Brackish water reverse osmosis study",
        url="https://example.com/paper",
        source_name="Journal",
        source_type="Publication",
        published_at="2099-01-01",
        abstract="A public abstract.",
        rule_score=7,
        matched_terms=["brackish water", "reverse osmosis"],
    )
    item_id, inserted = insert_item(db_path, item)
    duplicate_id, duplicate_inserted = insert_item(db_path, item)
    assert inserted is True
    assert duplicate_inserted is False
    assert duplicate_id == item_id
    rows = list_items(db_path, days=36500)
    assert len(rows) == 1
    assert json.loads(rows[0]["matched_terms"]) == ["brackish water", "reverse osmosis"]

    update_analysis(
        db_path,
        item_id,
        {
            "relevant": True,
            "relevance_score": 92,
            "tea_category": "Assumption Updates",
            "summary": "A bounded summary.",
            "why_it_matters": "Recovery may affect modeled water production.",
            "tea_parameters": ["recovery"],
            "numerical_evidence": ["Recovery was 80%."],
            "review_recommended": True,
            "technologies": ["reverse osmosis"],
            "topics": ["Brackish water"],
        },
        "test-model",
    )
    analyzed = list_items(db_path, days=36500)[0]
    assert analyzed["tea_category"] == "Assumption Updates"
    assert json.loads(analyzed["tea_parameters"]) == ["recovery"]
    assert analyzed["review_recommended"] == 1


def test_pipeline_can_collect_without_ai(tmp_path, monkeypatch):
    db_path = tmp_path / "intelligence.db"
    settings = IntelligenceSettings(db_path=db_path, max_items_per_run=10)
    item = IntelligenceItem(
        title="Produced water treatment update",
        url="https://example.com/update",
        source_name="Example",
        source_type="News",
        published_at="2099-01-01",
        snippet="Produced water treatment and beneficial reuse.",
        rule_score=8,
        matched_terms=["produced water", "beneficial reuse"],
    )
    monkeypatch.setitem(
        __import__("intelligence.pipeline", fromlist=["SOURCE_FETCHERS"]).SOURCE_FETCHERS,
        "rss",
        lambda _settings: [item],
    )
    stats = refresh_intelligence(settings, use_ai=False, sources=("rss",))
    assert stats.new_items == 1
    assert stats.summarized == 0
    assert latest_run(db_path)["status"] == "completed"


def test_pipeline_summarizes_item_collected_by_no_ai_run(tmp_path, monkeypatch):
    db_path = tmp_path / "intelligence.db"
    settings = IntelligenceSettings(db_path=db_path, max_items_per_run=10)
    item = IntelligenceItem(
        title="Produced water treatment update",
        url="https://example.com/update",
        source_name="Example",
        source_type="News",
        published_at="2099-01-01",
        snippet="Produced water treatment and beneficial reuse.",
        rule_score=8,
        matched_terms=["produced water", "beneficial reuse"],
    )
    pipeline = __import__("intelligence.pipeline", fromlist=["SOURCE_FETCHERS"])
    monkeypatch.setitem(pipeline.SOURCE_FETCHERS, "rss", lambda _settings: [item])
    refresh_intelligence(settings, use_ai=False, sources=("rss",))
    monkeypatch.setattr(
        pipeline,
        "analyze_with_ollama",
        lambda _item, _settings: {
            "relevant": True,
            "relevance_score": 95,
            "tea_category": "Technology Evidence",
            "summary": "Evidence-bounded summary.",
            "why_it_matters": "It concerns beneficial reuse.",
            "tea_parameters": ["recovery"],
            "numerical_evidence": [],
            "review_recommended": False,
            "technologies": [],
            "topics": ["Produced water"],
        },
    )
    stats = refresh_intelligence(settings, use_ai=True, sources=("rss",))
    assert stats.new_items == 0
    assert stats.summarized == 1
    result = list_items(db_path, days=36500)[0]
    assert result["summary"] == "Evidence-bounded summary."
    assert result["tea_category"] == "Technology Evidence"


def test_ollama_unknown_category_falls_back_to_background(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "message": {
                    "content": json.dumps({
                        "relevant": True,
                        "relevance_score": 65,
                        "tea_category": "General News",
                        "summary": "A bounded summary.",
                        "why_it_matters": "Provides market context.",
                        "tea_parameters": "not-an-array",
                        "numerical_evidence": [],
                        "review_recommended": False,
                        "technologies": [],
                        "topics": ["Produced water"],
                    })
                }
            }

    monkeypatch.setattr(
        "intelligence.summarizer.requests.post", lambda *args, **kwargs: FakeResponse()
    )
    item = IntelligenceItem(
        title="Produced water market update",
        url="https://example.com/news",
        source_name="Example",
        source_type="News",
        snippet="A public market update.",
    )
    result = analyze_with_ollama(item, IntelligenceSettings())
    assert result["tea_category"] == "Background Industry News"
    assert result["tea_parameters"] == []
