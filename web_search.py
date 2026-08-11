"""Real-time web search integration for My AI Agent."""

from __future__ import annotations

import os
from typing import Any

import requests


TAVILY_API_URL = "https://api.tavily.com/search"


def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the live web through Tavily and return normalized results."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured.")

    query = query.strip()
    if not query:
        return []

    response = requests.post(
        TAVILY_API_URL,
        json={
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": max(1, min(max_results, 10)),
            "include_answer": False,
            "include_raw_content": False,
        },
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json()
    results = []
    for item in payload.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0),
            }
        )
    return results
