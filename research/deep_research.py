"""Bounded deep-research orchestrator.

Uses the configured web search connector for evidence collection, then sends
those sources through the multi-agent review layer. It intentionally limits
iterations and source count to prevent recursive or runaway research.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from agent.multi_agent import run_multi_agent
from search.tavily import TavilyError, format_results, is_configured, search


class DeepResearchError(Exception):
    pass


def run_deep_research(query: str, *, preferred_provider: Optional[str] = None,
                      max_sources: int = 8) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        raise DeepResearchError("Research query cannot be empty.")
    if not is_configured():
        raise DeepResearchError("Tavily search is not configured.")

    safe_sources = max(2, min(int(max_sources), 8))
    try:
        result = search(query, search_depth="advanced", max_results=safe_sources, include_answer=True)
    except TavilyError as exc:
        raise DeepResearchError(str(exc)) from exc

    evidence = format_results(result)
    if not evidence:
        raise DeepResearchError("No useful research evidence was returned.")

    reviewed = run_multi_agent(
        query=query,
        context=evidence,
        max_agents=3,
        preferred_provider=preferred_provider,
    )
    reviewed["research_sources"] = result.get("results", [])[:safe_sources]
    reviewed["research_depth"] = "advanced"
    reviewed["source_count"] = len(reviewed["research_sources"])
    return reviewed
