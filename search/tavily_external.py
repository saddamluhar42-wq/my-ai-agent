from __future__ import annotations

import json
import urllib.request
from typing import Any

from config import TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3, TAVILY_URL

TIMEOUT = 4.5
MAX_RESULTS = 5


def _keys() -> list[str]:
    return [key for key in (TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3) if key]


def _request(key: str, query: str) -> list[dict[str, str]]:
    payload = {
        "query": query[:1600],
        "search_depth": "basic",
        "topic": "general",
        "max_results": MAX_RESULTS,
        "include_answer": False,
        "include_raw_content": False,
    }
    request = urllib.request.Request(
        TAVILY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    rows = data.get("results", [])
    return [
        {
            "title": str(row.get("title") or "Result"),
            "content": str(row.get("content") or ""),
            "url": str(row.get("url") or ""),
            "provider": "Tavily",
        }
        for row in rows[:MAX_RESULTS]
        if row.get("url")
    ]


def search(query: str) -> dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        return {"results": [], "provider": "Tavily", "key_index": None, "errors": []}

    errors: list[str] = []
    for index, key in enumerate(_keys(), start=1):
        try:
            results = _request(key, query)
            if results:
                return {
                    "results": results,
                    "provider": "Tavily",
                    "key_index": index,
                    "errors": errors,
                }
            errors.append(f"Tavily key {index}: empty results")
        except Exception as exc:
            errors.append(f"Tavily key {index}: {exc}")

    return {"results": [], "provider": "Tavily", "key_index": None, "errors": errors}


def is_configured() -> bool:
    return bool(_keys())
