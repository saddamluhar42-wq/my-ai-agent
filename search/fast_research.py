from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List

from config import (
    TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3, TAVILY_URL,
    YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3, YOU_SEARCH_URL,
)

SEARCH_TIMEOUT = 5.5
MAX_RESULTS_PER_PROVIDER = 5
MAX_TOTAL_RESULTS = 8


def _keys(*values: str | None) -> List[str]:
    return [x for x in values if x]


def _fetch_json(req: urllib.request.Request, timeout: float = SEARCH_TIMEOUT) -> Dict[str, Any]:
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _you(key: str, query: str) -> List[Dict[str, str]]:
    url = f"{YOU_SEARCH_URL}?{urllib.parse.urlencode({'query': query[:1800], 'count': MAX_RESULTS_PER_PROVIDER})}"
    req = urllib.request.Request(url, headers={"X-API-Key": key, "Accept": "application/json"})
    data = _fetch_json(req)
    rows = data.get("results", {}).get("web", [])
    return [{"title": r.get("title", "Result"), "content": r.get("description", ""), "url": r.get("url", ""), "provider": "You.com"} for r in rows[:MAX_RESULTS_PER_PROVIDER] if r.get("url")]


def _tavily(key: str, query: str) -> List[Dict[str, str]]:
    payload = {"query": query[:1800], "search_depth": "basic", "topic": "general", "max_results": MAX_RESULTS_PER_PROVIDER, "include_answer": False, "include_raw_content": False}
    req = urllib.request.Request(TAVILY_URL, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
    data = _fetch_json(req)
    return [{"title": r.get("title", "Result"), "content": r.get("content", ""), "url": r.get("url", ""), "provider": "Tavily"} for r in data.get("results", [])[:MAX_RESULTS_PER_PROVIDER] if r.get("url")]


def _wikipedia(query: str) -> List[Dict[str, str]]:
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query[:300], "srlimit": 3, "format": "json", "utf8": 1})
    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + params, headers={"User-Agent": "My-AI-Agent/1.0"})
    data = _fetch_json(req, timeout=3.5)
    rows = data.get("query", {}).get("search", [])
    out = []
    for r in rows[:3]:
        title = r.get("title", "")
        if title:
            out.append({"title": f"Wikipedia: {title}", "content": re.sub(r"<[^>]+>", " ", r.get("snippet", "")), "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")), "provider": "Wikipedia"})
    return out


def _quality(item: Dict[str, str]) -> int:
    url = item.get("url", "").lower()
    score = 0
    if ".gov" in url or ".gov." in url or ".edu" in url: score += 5
    if "wikipedia.org" in url: score += 2
    if "official" in url: score += 2
    if item.get("content"): score += min(2, len(item["content"]) // 250)
    return score


def research(query: str, deep: bool = False) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        return {"results": [], "providers": [], "errors": []}
    jobs = []
    keys = _keys(YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3)
    tavily_keys = _keys(TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3)
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        for key in keys: jobs.append(pool.submit(_you, key, query))
        for key in tavily_keys: jobs.append(pool.submit(_tavily, key, query))
        jobs.append(pool.submit(_wikipedia, query))
        results: List[Dict[str, str]] = []
        errors: List[str] = []
        for future in concurrent.futures.as_completed(jobs, timeout=SEARCH_TIMEOUT + 1.0):
            try:
                results.extend(future.result())
            except Exception as exc:
                errors.append(str(exc))
    unique = {}
    for item in results:
        url = item.get("url", "").strip()
        if url and url not in unique:
            unique[url] = item
    ranked = sorted(unique.values(), key=_quality, reverse=True)[:MAX_TOTAL_RESULTS if deep else 6]
    providers = sorted({x.get("provider", "") for x in ranked if x.get("provider")})
    blocks = []
    for item in ranked:
        blocks.append(f"- {item['title']}\n  {item.get('content','')[:1200]}\n  URL: {item['url']}")
    evidence = "LIVE WEB RESEARCH RESULTS\n" + "\n".join(blocks) if blocks else ""
    return {"evidence": evidence, "results": ranked, "providers": providers, "result_count": len(ranked), "errors": errors}
