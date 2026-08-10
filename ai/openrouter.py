import json
import urllib.error
import urllib.request

from config import (
    AI_TEMPERATURE,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
    RENDER_URL,
    REQUEST_TIMEOUT,
)


class OpenRouterError(Exception):
    """Raised when OpenRouter API fails."""


def is_configured():
    return bool(OPENROUTER_API_KEY)


def generate(
    prompt,
    temperature=None,
    max_tokens=None,
):
    if not OPENROUTER_API_KEY:
        raise OpenRouterError(
            "OPENROUTER_API_KEY is not configured."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": (
            AI_TEMPERATURE
            if temperature is None
            else temperature
        ),
    }

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": "application/json",
            "HTTP-Referer": RENDER_URL,
            "X-Title": "My AI Agent",
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

        raise OpenRouterError(
            f"OpenRouter HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise OpenRouterError(
            f"OpenRouter network error: {error}"
        ) from error

    except Exception as error:
        raise OpenRouterError(
            f"OpenRouter request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise OpenRouterError(
            "OpenRouter returned invalid JSON."
        ) from error

    if "error" in result:
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "OpenRouter API error.",
            )
        else:
            message = str(error_data)

        raise OpenRouterError(message)

    choices = result.get(
        "choices",
        [],
    )

    if not choices:
        raise OpenRouterError(
            "OpenRouter returned no choices."
        )

    message = choices[0].get(
        "message",
        {},
    )

    answer = message.get(
        "content",
        "",
    )

    if isinstance(answer, list):
        answer = "".join(
            item.get("text", "")
            for item in answer
            if isinstance(item, dict)
        )

    answer = str(answer).strip()

    if not answer:
        raise OpenRouterError(
            "OpenRouter returned an empty response."
        )

    return answer


def get_provider_info():
    return {
        "provider": "OpenRouter",
        "model": OPENROUTER_MODEL,
        "configured": is_configured(),
    }
