"""Research policy and source-quality rules for My AI Agent.

This module is intentionally provider-agnostic. It defines when live research is
mandatory and how retrieved sources should be ranked before synthesis.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable


class ResearchMode(str, Enum):
    DIRECT = "direct"
    WEB = "web"
    DEEP = "deep"


@dataclass(frozen=True)
class SourceRecord:
    url: str
    title: str = ""
    domain: str = ""
    source_type: str = "web"
    published_at: str | None = None
    score: float = 0.0


# Current/fresh facts must not be answered from model memory alone.
CURRENT_TERMS = {
    "today", "now", "latest", "current", "recent", "this week", "this month",
    "price", "rate", "weather", "stock", "share price", "exchange rate",
    "news", "update", "updates", "status", "live", "available now",
}

RESEARCH_TERMS = {
    "research", "study", "studies", "paper", "papers", "history", "historical",
    "evidence", "sources", "source", "compare", "comparison", "analysis",
    "deep dive", "investigate", "investigation", "why", "how does", "review",
    "literature", "statistics", "data", "facts", "origins", "origin",
}

# Prefer authoritative/primary material over aggregators. Wikipedia is a discovery
# and cross-reference layer, not an automatic final authority.
PRIMARY_DOMAIN_HINTS = (
    ".gov", ".gov.in", ".edu", ".ac.uk", "who.int", "un.org", "worldbank.org",
    "oecd.org", "nih.gov", "pubmed.ncbi.nlm.nih.gov", "nature.com", "science.org",
    "nasa.gov", "archives.gov", "loc.gov", "europa.eu",
)
WIKIPEDIA_DOMAINS = ("wikipedia.org", "wikidata.org")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def requires_web_research(query: str) -> bool:
    """Return True whenever an answer should be grounded in live web evidence."""
    q = _normalize(query)
    if not q:
        return False
    if any(term in q for term in CURRENT_TERMS):
        return True
    if any(term in q for term in RESEARCH_TERMS):
        return True
    # Questions asking for factual claims should be grounded when ambiguous.
    if q.endswith("?") and len(q.split()) >= 5:
        return True
    return False


def research_mode(query: str) -> ResearchMode:
    q = _normalize(query)
    if not requires_web_research(q):
        return ResearchMode.DIRECT
    deep_signals = ("deep research", "comprehensive", "thorough", "in depth", "literature review", "investigate")
    if any(x in q for x in deep_signals):
        return ResearchMode.DEEP
    return ResearchMode.WEB


def source_quality(source: SourceRecord) -> float:
    """Score source quality; freshness is handled by the caller when timestamps exist."""
    url = _normalize(source.url)
    domain = _normalize(source.domain)
    score = float(source.score or 0.0)
    if any(hint in domain or hint in url for hint in PRIMARY_DOMAIN_HINTS):
        score += 0.40
    if any(domain.endswith(d) or d in url for d in WIKIPEDIA_DOMAINS):
        score += 0.15
    if source.source_type.lower() in {"primary", "official", "academic", "peer_reviewed"}:
        score += 0.35
    elif source.source_type.lower() in {"secondary", "reputable_news", "specialist"}:
        score += 0.20
    return min(score, 1.0)


def rank_sources(sources: Iterable[SourceRecord]) -> list[SourceRecord]:
    """Rank sources for synthesis; never discard lower-ranked sources silently."""
    return sorted(sources, key=source_quality, reverse=True)


def research_system_rules() -> str:
    return """RESEARCH POLICY:
- Use live web research whenever the query asks for current, recent, factual, comparative, historical, evidence-based, or research information.
- For research tasks, do not rely on model memory alone.
- Search broadly, then narrow to authoritative, primary, academic, official, specialist, and reputable sources.
- Use Wikipedia as a discovery/context/cross-reference layer and inspect its references; do not treat Wikipedia alone as proof when stronger sources exist.
- Cross-check important claims against independent sources.
- Detect and explicitly report meaningful source conflicts.
- Prefer recent sources for fast-changing facts and primary/official sources for claims about an organization, product, policy, price, or event.
- Never invent a current value when live evidence is unavailable. State that live verification failed instead.
- Preserve source URLs/titles so the final answer can cite the evidence behind material claims.
- Separate verified facts, reasonable inference, and uncertainty in the final synthesis.
"""
