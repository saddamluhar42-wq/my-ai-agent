import json
import urllib.error
import urllib.request

from config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    ANTHROPIC_API_KEY,
    ANTHROPIC_API_KEY_2,
    ANTHROPIC_API_KEY_3,
    ANTHROPIC_MODEL,
    ANTHROPIC_URL,
    REQUEST_TIMEOUT,
)


class AnthropicError(Exception):
    """Raised when Anthropic API fails."""


def is_configured():
    return bool(
        ANTHROPIC_API_KEY
        or ANTHROPIC_API_KEY_2
        or ANTHROPIC_API_KEY_3
    )


def _generate_with_key(
    api_key,
    prompt,
    temperature=None,
    max_tokens=None,
):
    if not api_key:
        raise AnthropicError(
            "Anthropic API key is not configured."
        )

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": (
            AI_MAX_OUTPUT_TOKENS
            if max_tokens is None
            else max_tokens
        ),
        "temperature": (
            AI_TEMPERATURE
            if temperature is None
            else temperature
        ),
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
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

        raise AnthropicError(
            f"Anthropic HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise AnthropicError(
            f"Anthropic network error: {error}"
        ) from error

    except Exception as error:
        raise AnthropicError(
            f"Anthropic request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise AnthropicError(
            "Anthropic returned invalid JSON."
        ) from error

    if "error" in result:
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "Anthropic API error.",
            )
        else:
            message = str(error_data)

        raise AnthropicError(message)

    content = result.get(
        "content",
        [],
    )

    if not content:
        raise AnthropicError(
            "Anthropic returned no content."
        )

    answer_parts = []

    for item in content:
        if not isinstance(item, dict):
            continue

        if item.get("type") == "text":
            answer_parts.append(
                item.get("text", "")
            )

    answer = "".join(
        answer_parts
    ).strip()

    if not answer:
        raise AnthropicError(
            "Anthropic returned an empty response."
        )

    return answer


def generate(
    prompt,
    temperature=None,
    max_tokens=None,
):
    keys = [
        (
            "Anthropic",
            ANTHROPIC_API_KEY,
        ),
        (
            "Anthropic-2",
            ANTHROPIC_API_KEY_2,
        ),
        (
            "Anthropic-3",
            ANTHROPIC_API_KEY_3,
        ),
    ]

    errors = []

    for provider_name, api_key in keys:
        if not api_key:
            continue

        try:
            answer = _generate_with_key(
                api_key=api_key,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "answer": answer,
                "provider": provider_name,
                "model": ANTHROPIC_MODEL,
            }

        except Exception as error:
            errors.append(
                f"{provider_name}: {error}"
            )

    if not errors:
        raise AnthropicError(
            "No Anthropic API key is configured."
        )

    raise AnthropicError(
        "All Anthropic keys failed.\n"
        + "\n".join(errors)
    )


def get_provider_info():
    return {
        "provider": "Anthropic",
        "model": ANTHROPIC_MODEL,
        "configured": is_configured(),
        "keys_configured": sum(
            bool(key)
            for key in [
                ANTHROPIC_API_KEY,
                ANTHROPIC_API_KEY_2,
                ANTHROPIC_API_KEY_3,
            ]
        ),
    }
