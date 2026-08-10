import json
import urllib.error
import urllib.request

from config import (
    REQUEST_TIMEOUT,
    TAVILY_API_KEY,
    TAVILY_URL,
)


class TavilyError(Exception):
    """Raised when Tavily search fails."""


def is_configured():
    return bool(TAVILY_API_KEY)


def search(
    query,
    search_depth="advanced",
    max_results=5,
    include_answer=True,
):
    if not TAVILY_API_KEY:
        raise TavilyError(
            "TAVILY_API_KEY is not configured."
        )

    if not query or not query.strip():
        raise TavilyError(
            "Search query cannot be empty."
        )

    safe_max_results = max(
        1,
        min(int(max_results), 10),
    )

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query.strip(),
        "search_depth": search_depth,
        "include_answer": include_answer,
        "max_results": safe_max_results,
    }

    request = urllib.request.Request(
        TAVILY_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            raw = response.read().decode(
                "utf-8"
            )

    except urllib.error.HTTPError as error:
        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise TavilyError(
            f"Tavily HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise TavilyError(
            f"Tavily network error: {error}"
        ) from error

    except Exception as error:
        raise TavilyError(
            f"Tavily request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise TavilyError(
            "Tavily returned invalid JSON."
        ) from error

    if "error" in result:
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "Tavily API error.",
            )
        else:
            message = str(error_data)

        raise TavilyError(message)

    return result


def get_answer(result):
    if not result:
        return ""

    return str(
        result.get(
            "answer",
            "",
        )
    ).strip()


def get_sources(result):
    if not result:
        return []

    sources = []

    for item in result.get(
        "results",
        [],
    ):
        if not isinstance(item, dict):
            continue

        sources.append(
            {
                "title": item.get(
                    "title",
                    "",
                ),
                "url": item.get(
                    "url",
                    "",
                ),
                "content": item.get(
                    "content",
                    "",
                ),
                "score": item.get(
                    "score"
                ),
            }
        )

    return sources


def format_results(result):
    if not result:
        return "No web search results."

    parts = []

    answer = get_answer(result)

    if answer:
        parts.append(
            "WEB SEARCH ANSWER:\n"
            + answer
        )

    sources = get_sources(result)

    if sources:
        source_text = []

        for index, source in enumerate(
            sources,
            start=1,
        ):
            source_text.append(
                f"SOURCE {index}\n"
                f"TITLE: {source['title']}\n"
                f"URL: {source['url']}\n"
                f"CONTENT: {source['content']}"
            )

        parts.append(
            "WEB SOURCES:\n"
            + "\n\n".join(source_text)
        )

    if not parts:
        return "No useful web search information found."

    return "\n\n".join(parts)
