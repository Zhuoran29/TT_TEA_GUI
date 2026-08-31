"""Local Ollama relevance review and evidence-bounded summarization."""

from __future__ import annotations

import json

import requests

from .config import IntelligenceSettings
from .models import IntelligenceItem


SYSTEM_PROMPT = """You curate TEA Intelligence for Nontraditional Water Treatment.
Use only the supplied title and evidence text. Never invent methods, results, conclusions, costs,
or full-text details that are absent. Return JSON only. Include an item only when it directly concerns
produced water, oilfield wastewater, brackish water, brackish groundwater, their treatment, reuse,
concentrate, regulation, funding, or a clearly applicable treatment technology. Assess usefulness for
techno-economic analysis even when the source does not use the term TEA."""


def analyze_with_ollama(item: IntelligenceItem, settings: IntelligenceSettings) -> dict:
    prompt = f"""Review this public item for a treatment-train techno-economic analysis tool.

Source type: {item.source_type}
Title: {item.title}
Evidence basis: {item.summary_basis}
Evidence text:
{item.summary_source[:12000]}

Choose the single best category using these rules:
- Assumption Updates: direct quantitative evidence that may change a technical or economic input.
- Technology Evidence: measured performance, reliability, fouling, residuals, or scale-up evidence.
- Cost & Project Signals: costs, capacity, awards, contracts, construction, or commercial deployment.
- Policy Impact: a regulatory or permitting change with a plausible compliance or cost effect.
- Funding Opportunities: an actionable grant, solicitation, prize, deadline, or cost-share notice.
- Background Industry News: relevant context without enough evidence for one of the categories above.
Do not promote an item merely because it mentions produced water or a treatment technology.

Return one JSON object with exactly these fields:
- relevant: boolean; true only if worth including in this focused intelligence page
- relevance_score: integer from 0 to 100 measuring usefulness for TEA decisions
- tea_category: exactly one of Assumption Updates, Technology Evidence, Cost & Project Signals,
  Policy Impact, Funding Opportunities, Background Industry News
- summary: no more than 100 words; empty if evidence is insufficient
- why_it_matters: one evidence-bounded sentence explaining the possible TEA impact; empty if not relevant
- tea_parameters: array of potentially affected parameters, such as CAPEX, OPEX, energy intensity,
  chemical consumption, recovery, removal efficiency, membrane life, residuals disposal, capacity,
  financing, or regulatory compliance cost
- numerical_evidence: array of exact short facts with numbers and units explicitly stated in the evidence
- review_recommended: boolean; true when the evidence may justify reviewing a model assumption
- technologies: array of technology names explicitly mentioned
- topics: array selected from Produced water, Brackish water, Desalination, Pretreatment,
  Fouling and scaling, Brine management, Beneficial reuse, Policy, Funding, Other
"""
    response = requests.post(
        f"{settings.ollama_url.rstrip('/')}/api/chat",
        json={
            "model": settings.ollama_model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 350},
        },
        timeout=settings.ollama_timeout,
    )
    response.raise_for_status()
    content = response.json().get("message", {}).get("content", "")
    result = json.loads(content)
    required = {
        "relevant", "relevance_score", "tea_category", "summary", "why_it_matters",
        "tea_parameters", "numerical_evidence", "review_recommended", "technologies", "topics",
    }
    if not required.issubset(result):
        raise ValueError("Ollama response is missing required fields")
    result["relevance_score"] = max(0, min(100, int(result["relevance_score"])))
    for field in ("technologies", "topics", "tea_parameters", "numerical_evidence"):
        if not isinstance(result[field], list):
            result[field] = []
    allowed_categories = {
        "Assumption Updates", "Technology Evidence", "Cost & Project Signals",
        "Policy Impact", "Funding Opportunities", "Background Industry News",
    }
    if result["tea_category"] not in allowed_categories:
        result["tea_category"] = "Background Industry News"
    return result


def ollama_health(settings: IntelligenceSettings) -> tuple[bool, str]:
    try:
        response = requests.get(
            f"{settings.ollama_url.rstrip('/')}/api/tags", timeout=5
        )
        response.raise_for_status()
        names = [model.get("name", "") for model in response.json().get("models", [])]
        available = settings.ollama_model in names or any(
            name.split(":", 1)[0] == settings.ollama_model.split(":", 1)[0] for name in names
        )
        if not available:
            return False, f"Ollama is running, but {settings.ollama_model} is not installed."
        return True, f"Ollama is ready with {settings.ollama_model}."
    except requests.RequestException as exc:
        return False, f"Cannot reach Ollama at {settings.ollama_url}: {exc}"
