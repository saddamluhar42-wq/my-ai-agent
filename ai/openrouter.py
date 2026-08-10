import json
import urllib.error
import urllib.request

from config import (
    AI_TEMPERATURE,
    OPENROUTER_API_KEY,
    OPENROUTER_API_KEY_2,
    OPENROUTER_MODEL,
    OPENROUTER_MODEL_2,
    OPENROUTER_URL,
    OPENROUTER_URL_2,
    RENDER_URL,
    REQUEST_TIMEOUT,
)


class OpenRouterError(Exception):
    """Raised when OpenRouter API fails."""


def is_configured():
    return bool(
        OPENROUTER_API_KEY
        or OPENROUTER_API_KEY_2
    )


def _generate_with_key(
    api_key,
    model,
    url,
    prompt,
    temperature=None,
    max_tokens=None,
):
    if not api_key:
        raise OpenRouterError(
            "OpenRouter API key is not configured."
        )

    payload = {
        "model": model,
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
        url,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {api_key}"
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


def generate(
    prompt,
    temperature=None,
    max_tokens=None,
):
    errors = []

    keys = [
        {
            "name": "OpenRouter",
            "key": OPENROUTER_API_KEY,
            "model": OPENROUTER_MODEL,
            "url": OPENROUTER_URL,
        },
        {
            "name": "OpenRouter-2",
            "key": OPENROUTER_API_KEY_2,
            "model": OPENROUTER_MODEL_2,
            "url": OPENROUTER_URL_2,
        },
    ]

    for item in keys:
        if not item["key"]:
            continue

        try:
            answer = _generate_with_key(
                api_key=item["key"],
                model=item["model"],
                url=item["url"],
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "answer": answer,
                "provider": item["name"],
                "model": item["model"],
            }

        except Exception as error:
            errors.append(
                f'{item["name"]}: {error}'
            )

    if not errors:
        raise OpenRouterError(
            "No OpenRouter API key is configured."
        )

    raise OpenRouterError(
        "All OpenRouter keys failed.\n"
        + "\n".join(errors)
    )


def get_provider_info():
    return {
        "provider": "OpenRouter",
        "model": OPENROUTER_MODEL,
        "configured": is_configured(),
        "keys_configured": sum(
            bool(key)
            for key in [
                OPENROUTER_API_KEY,
                OPENROUTER_API_KEY_2,
            ]
        ),
    }
