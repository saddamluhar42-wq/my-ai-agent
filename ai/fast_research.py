from __future__ import annotations

import concurrent.futures
import json
import urllib.parse
import urllib.request

from config import (
    YDC_API_KEY,
    YDC_API_KEY_2,
    YDC_API_KEY_3,
    TAVILY_API_KEY,
    TAVILY_API_KEY_2,
    TAVILY_API_KEY_3,
    YOU_SEARCH_URL,
    TAVILY_URL,
)

FAST_TIMEOUT = 8
MAX_RESULTS = 5


def _keys(*values):
    return [value for value in values if value]


def _you(key, query):
    url = f"{YOU_SEARCH_URL}?query={urllib.parse.quote(query[:2500])}&count={MAX_RESULTS}"
    req = urllib.request.Request(url, headers={"X-API-Key": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=FAST_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    results = data.get("results", {}).get("web", [])[:MAX_RESULTS]
    if not results:
        raise RuntimeError("You.com returned no results")
    return "You.com", results


def _tavily(key, query):
    payload = {
        "query": query[:2500],
        "search_depth": "basic",
        "topic": "general",
        "max_results": MAX_RESULTS,
        "include_answer": False,
        "include_raw_content": False,
    }
    req = urllib.request.Request(
        TAVILY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=FAST_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    results = data.get("results", [])[:MAX_RESULTS]
    if not results:
        raise RuntimeError("Tavily returned no results")
    return "Tavily", results


def _run(fn, key, query):
    try:
        return fn(key, query)
    except Exception:
        return None


def search(query, deep=False):
    """Fast parallel web retrieval. Successful providers are merged; failed keys are ignored."""
    jobs = []
    for key in _keys(YDC_API_KEY, YDC_API_KEY_2, YDC_API_KEY_3):
        jobs.append((_you, key))
    if deep:
        for key in _keys(TAVILY_API_KEY, TAVILY_API_KEY_2, TAVILY_API_KEY_3):
            jobs.append((_tavily, key))

    if not jobs:
        raise RuntimeError("No web search API keys configured")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(_run, fn, key, query) for fn, key in jobs]
        # Collect the first successful provider quickly. For deep research, collect all.
        for future in concurrent.futures.as_completed(futures, timeout=FAST_TIMEOUT + 1):
            result = future.result()
            if result:
                results.append(result)
                if not deep:
                    for other in futures:
                        if not other.done():
                            other.cancel()
                    break

    if not results:
        raise RuntimeError("All web search providers failed")

    seen = set()
    lines = []
    providers = []
    for provider, items in results:
        providers.append(provider)
        for item in items:
            url = item.get("url", "") or item.get("link", "")
            if not url or url in seen:
                continue
            seen.add(url)
            title = item.get("title", "Result")
            text = item.get("description", "") or item.get("content", "")
            lines.append(f"- {title}\n  {text}\n  URL: {url}")

    return {
        "evidence": "LIVE WEB RESULTS\n" + "\n".join(lines[:10]),
        "providers": list(dict.fromkeys(providers)),
        "result_count": min(len(lines), 10),
    }
