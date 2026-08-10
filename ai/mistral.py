import json
import urllib.error
import urllib.request

from config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    MISTRAL_URL,
    REQUEST_TIMEOUT,
)


class MistralError(Exception):
    """Raised when Mistral API fails."""


def is_configured():
    return bool(MISTRAL_API_KEY)


def generate(
    prompt,
    temperature=None,
    max_tokens=None,
):
    if not MISTRAL_API_KEY:
        raise MistralError(
            "MISTRAL_API_KEY is not configured."
        )

    payload = {
        "model": MISTRAL_MODEL,
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
        "max_tokens": (
            AI_MAX_OUTPUT_TOKENS
            if max_tokens is None
            else max_tokens
        ),
    }

    request = urllib.request.Request(
        MISTRAL_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {MISTRAL_API_KEY}"
            ),
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

        raise MistralError(
            f"Mistral HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise MistralError(
            f"Mistral network error: {error}"
        ) from error

    except Exception as error:
        raise MistralError(
            f"Mistral request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise MistralError(
            "Mistral returned invalid JSON."
        ) from error

    if "error" in result:
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "Mistral API error.",
            )
        else:
            message = str(error_data)

        raise MistralError(message)

    choices = result.get(
        "choices",
        [],
    )

    if not choices:
        raise MistralError(
            "Mistral returned no choices."
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
        raise MistralError(
            "Mistral returned an empty response."
        )

    return answer


def get_provider_info():
    return {
        "provider": "Mistral",
        "model": MISTRAL_MODEL,
        "configured": is_configured(),
    }
