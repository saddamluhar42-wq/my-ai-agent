"""Bounded research loop for acquiring and verifying external knowledge."""

from __future__ import annotations

from typing import Any, Dict, List

from knowledge.universal_hub import upsert_knowledge
from search.tavily import TavilyError, get_answer, get_sources, is_configured, search


class ResearchLoop:
    """Researches a topic, stores source evidence, and returns a research packet.

    The loop is intentionally bounded. It does not recursively browse forever and
    it never treats web content as executable instructions.
    """

    def __init__(self, max_sources: int = 6):
        self.max_sources = max(1, min(int(max_sources), 10))

    def research(self, query: str, *, domain: str = "research") -> Dict[str, Any]:
        query = str(query or "").strip()
        if not query:
            return {"success": False, "reason": "empty_query", "sources": []}
        if not is_configured():
            return {"success": False, "reason": "web_search_not_configured", "sources": []}
        try:
            result = search(query, search_depth="advanced", max_results=self.max_sources, include_answer=True)
        except TavilyError as error:
            return {"success": False, "reason": str(error), "sources": []}

        stored: List[Dict[str, Any]] = []
        for source in get_sources(result)[: self.max_sources]:
            url = str(source.get("url") or "").strip()
            content = str(source.get("content") or "").strip()
            title = str(source.get("title") or "").strip()
            if not content:
                continue
            source_id = upsert_knowledge(
                content,
                domain=domain,
                title=title,
                source_type="web_research",
                source_name=title or "web source",
                source_url=url or None,
                trust_score=0.65,
                freshness_score=1.0,
                metadata={
                    "research_query": query,
                    "search_score": source.get("score"),
                    "acquired_by": "bounded_research_loop",
                },
            )
            stored.append({"id": source_id, "title": title, "url": url, "score": source.get("score")})

        return {
            "success": True,
            "query": query,
            "answer": get_answer(result),
            "sources": stored,
            "stored_count": len(stored),
        }


research_loop = ResearchLoop()


def research_topic(query: str, *, domain: str = "research") -> Dict[str, Any]:
    return research_loop.research(query, domain=domain)
