import json
import urllib.error
import urllib.request

from config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_URL,
    REQUEST_TIMEOUT,
)


class GeminiError(Exception):
    """Raised when Gemini API fails."""


def is_configured():
    return bool(GEMINI_API_KEY)


def generate(
    prompt,
    temperature=None,
    max_output_tokens=None,
):
    if not GEMINI_API_KEY:
        raise GeminiError(
            "GEMINI_API_KEY is not configured."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": (
                AI_TEMPERATURE
                if temperature is None
                else temperature
            ),
            "maxOutputTokens": (
                AI_MAX_OUTPUT_TOKENS
                if max_output_tokens is None
                else max_output_tokens
            ),
        },
    }

    request = urllib.request.Request(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
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

        raise GeminiError(
            f"Gemini HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise GeminiError(
            f"Gemini network error: {error}"
        ) from error

    except Exception as error:
        raise GeminiError(
            f"Gemini request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise GeminiError(
            "Gemini returned invalid JSON."
        ) from error

    if "error" in result:
        raise GeminiError(
            result["error"].get(
                "message",
                "Gemini API error.",
            )
        )

    candidates = result.get(
        "candidates",
        [],
    )

    if not candidates:
        raise GeminiError(
            "Gemini returned no candidates."
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    answer = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
    ).strip()

    if not answer:
        raise GeminiError(
            "Gemini returned an empty response."
        )

    return answer


def get_provider_info():
    return {
        "provider": "Gemini",
        "model": GEMINI_MODEL,
        "configured": is_configured(),
    }
