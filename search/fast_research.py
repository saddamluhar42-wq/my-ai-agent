from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from config import TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3, TAVILY_URL, YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3, YOU_SEARCH_URL

SEARCH_TIMEOUT = 4.5
MAX_RESULTS_PER_PROVIDER = 4
MAX_TOTAL_RESULTS = 6


def _keys(*values: str | None) -> List[str]: return [x for x in values if x]

def _fetch_json(req: urllib.request.Request, timeout: float = SEARCH_TIMEOUT) -> Dict[str, Any]:
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _you(key: str, query: str) -> List[Dict[str, str]]:
    url = f"{YOU_SEARCH_URL}?{urllib.parse.urlencode({'query': query[:1600], 'count': MAX_RESULTS_PER_PROVIDER})}"
    req = urllib.request.Request(url, headers={"X-API-Key": key, "Accept": "application/json"})
    rows = _fetch_json(req).get("results", {}).get("web", [])
    return [{"title": r.get("title", "Result"), "content": r.get("description", ""), "url": r.get("url", ""), "provider": "You.com"} for r in rows[:MAX_RESULTS_PER_PROVIDER] if r.get("url")]

def _tavily(key: str, query: str) -> List[Dict[str, str]]:
    payload = {"query": query[:1600], "search_depth": "basic", "topic": "general", "max_results": MAX_RESULTS_PER_PROVIDER, "include_answer": False, "include_raw_content": False}
    req = urllib.request.Request(TAVILY_URL, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
    rows = _fetch_json(req).get("results", [])
    return [{"title": r.get("title", "Result"), "content": r.get("content", ""), "url": r.get("url", ""), "provider": "Tavily"} for r in rows[:MAX_RESULTS_PER_PROVIDER] if r.get("url")]

def _wikipedia(query: str) -> List[Dict[str, str]]:
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query[:300], "srlimit": 3, "format": "json", "utf8": 1})
    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + params, headers={"User-Agent": "My-AI-Agent/2.2"})
    rows = _fetch_json(req, timeout=3.0).get("query", {}).get("search", [])
    return [{"title": f"Wikipedia: {r.get('title','')}", "content": re.sub(r"<[^>]+>", " ", r.get("snippet", "")), "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(r.get("title", "").replace(" ", "_")), "provider": "Wikipedia"} for r in rows[:3] if r.get("title")]

def _quality(item: Dict[str, str]) -> int:
    url = item.get("url", "").lower()
    score = 0
    if ".gov" in url or ".edu" in url: score += 5
    if "wikipedia.org" in url: score += 2
    if ".org" in url: score += 1
    if item.get("content"): score += min(2, len(item["content"]) // 250)
    return score

def research(query: str, deep: bool = False) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query: return {"evidence": "", "results": [], "providers": [], "result_count": 0, "errors": []}
    futures = []
    keys = _keys(YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3)
    tavily_keys = _keys(TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3)
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        futures += [pool.submit(_you, key, query) for key in keys]
        futures += [pool.submit(_tavily, key, query) for key in tavily_keys]
        futures.append(pool.submit(_wikipedia, query))
        results, errors = [], []
        for future in futures:
            try: results.extend(future.result(timeout=SEARCH_TIMEOUT + 0.5))
            except Exception as exc: errors.append(str(exc))
    unique = {}
    for item in results:
        url = item.get("url", "").strip()
        if url: unique.setdefault(url, item)
    ranked = sorted(unique.values(), key=_quality, reverse=True)[:MAX_TOTAL_RESULTS if deep else 5]
    providers = sorted({x.get("provider", "") for x in ranked if x.get("provider")})
    evidence = "LIVE WEB RESEARCH RESULTS\n" + "\n".join(f"- {x['title']}\n  {x.get('content','')[:1000]}\n  URL: {x['url']}" for x in ranked) if ranked else ""
    return {"evidence": evidence, "results": ranked, "providers": providers, "result_count": len(ranked), "errors": errors}
