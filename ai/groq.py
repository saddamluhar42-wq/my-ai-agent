import json
import urllib.error
import urllib.request

from config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_URL,
    REQUEST_TIMEOUT,
)


class GroqError(Exception):
    """Raised when Groq API fails."""


def is_configured():
    return bool(GROQ_API_KEY)


def generate(
    prompt,
    temperature=None,
    max_tokens=None,
):
    if not GROQ_API_KEY:
        raise GroqError(
            "GROQ_API_KEY is not configured."
        )

    payload = {
        "model": GROQ_MODEL,
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
        GROQ_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {GROQ_API_KEY}"
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

        raise GroqError(
            f"Groq HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise GroqError(
            f"Groq network error: {error}"
        ) from error

    except Exception as error:
        raise GroqError(
            f"Groq request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise GroqError(
            "Groq returned invalid JSON."
        ) from error

    if "error" in result:
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "Groq API error.",
            )
        else:
            message = str(error_data)

        raise GroqError(message)

    choices = result.get(
        "choices",
        [],
    )

    if not choices:
        raise GroqError(
            "Groq returned no choices."
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
        raise GroqError(
            "Groq returned an empty response."
        )

    return answer


def get_provider_info():
    return {
        "provider": "Groq",
        "model": GROQ_MODEL,
        "configured": is_configured(),
    }
