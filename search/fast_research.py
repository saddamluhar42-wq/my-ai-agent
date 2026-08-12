from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from config import YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3, YOU_SEARCH_URL
from search.tavily_external import is_configured as tavily_configured
from search.tavily_external import search as tavily_search

SEARCH_TIMEOUT = 4.5
MAX_RESULTS_PER_PROVIDER = 4
MAX_TOTAL_RESULTS = 6


def _keys(*values: str | None) -> List[str]:
    return [x for x in values if x]


def _fetch_json(req: urllib.request.Request, timeout: float = SEARCH_TIMEOUT) -> Dict[str, Any]:
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _you(key: str, query: str) -> List[Dict[str, str]]:
    url = f"{YOU_SEARCH_URL}?{urllib.parse.urlencode({'query': query[:1600], 'count': MAX_RESULTS_PER_PROVIDER})}"
    req = urllib.request.Request(url, headers={"X-API-Key": key, "Accept": "application/json"})
    rows = _fetch_json(req).get("results", {}).get("web", [])
    return [
        {"title": r.get("title", "Result"), "content": r.get("description", ""), "url": r.get("url", ""), "provider": "You.com"}
        for r in rows[:MAX_RESULTS_PER_PROVIDER]
        if r.get("url")
    ]


def _wikipedia(query: str) -> List[Dict[str, str]]:
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query[:300], "srlimit": 3, "format": "json", "utf8": 1})
    req = urllib.request.Request(
        "https://en.wikipedia.org/w/api.php?" + params,
        headers={"User-Agent": "My-AI-Agent/2.2"},
    )
    rows = _fetch_json(req, timeout=3.0).get("query", {}).get("search", [])
    return [
        {
            "title": f"Wikipedia: {r.get('title', '')}",
            "content": re.sub(r"<[^>]+>", " ", r.get("snippet", "")),
            "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(r.get("title", "").replace(" ", "_")),
            "provider": "Wikipedia",
        }
        for r in rows[:3]
        if r.get("title")
    ]


def _quality(item: Dict[str, str]) -> int:
    url = item.get("url", "").lower()
    score = 0
    if ".gov" in url or ".edu" in url:
        score += 5
    if "wikipedia.org" in url:
        score += 2
    if ".org" in url:
        score += 1
    if item.get("content"):
        score += min(2, len(item["content"]) // 250)
    return score


def _dedupe_and_rank(results: List[Dict[str, str]], deep: bool) -> List[Dict[str, str]]:
    unique: Dict[str, Dict[str, str]] = {}
    for item in results:
        url = item.get("url", "").strip()
        if url:
            unique.setdefault(url, item)
    return sorted(unique.values(), key=_quality, reverse=True)[:MAX_TOTAL_RESULTS if deep else 5]


def _fallback_search(query: str) -> tuple[List[Dict[str, str]], List[str]]:
    """Use existing search engines only after the external Tavily connector fails."""
    results: List[Dict[str, str]] = []
    errors: List[str] = []
    keys = _keys(YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3)

    for index, key in enumerate(keys, start=1):
        try:
            results.extend(_you(key, query))
            if results:
                break
        except Exception as exc:
            errors.append(f"You.com key {index}: {exc}")

    if not results:
        try:
            results.extend(_wikipedia(query))
        except Exception as exc:
            errors.append(f"Wikipedia: {exc}")

    return results, errors


def research(query: str, deep: bool = False) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        return {"evidence": "", "results": [], "providers": [], "result_count": 0, "errors": []}

    results: List[Dict[str, str]] = []
    errors: List[str] = []
    primary_used = False
    fallback_used = False
    tavily_key_index = None

    # External Tavily is the primary search service. Its three Render keys are
    # rotated sequentially; backup engines are not called when Tavily succeeds.
    if tavily_configured():
        primary_used = True
        tavily = tavily_search(query)
        results.extend(tavily.get("results", []))
        errors.extend(tavily.get("errors", []))
        tavily_key_index = tavily.get("key_index")

    # Existing search engines remain as a true fallback path.
    if not results:
        fallback_used = True
        fallback_results, fallback_errors = _fallback_search(query)
        results.extend(fallback_results)
        errors.extend(fallback_errors)

    ranked = _dedupe_and_rank(results, deep=deep)
    providers = sorted({x.get("provider", "") for x in ranked if x.get("provider")})
    evidence = (
        "LIVE WEB RESEARCH RESULTS\n"
        + "\n".join(
            f"- {x['title']}\n  {x.get('content', '')[:1000]}\n  URL: {x['url']}"
            for x in ranked
        )
        if ranked
        else ""
    )
    return {
        "evidence": evidence,
        "results": ranked,
        "providers": providers,
        "result_count": len(ranked),
        "errors": errors,
        "primary": "Tavily" if primary_used else None,
        "fallback_used": fallback_used,
        "tavily_key_index": tavily_key_index,
    }
