import json
import urllib.error
import urllib.request

from config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    GEMINI_API_KEY,
    GEMINI_API_KEY_2,
    GEMINI_MODEL,
    GEMINI_MODEL_2,
    GEMINI_URL,
    GEMINI_URL_2,
    REQUEST_TIMEOUT,
)


class GeminiError(Exception):
    """Raised when Gemini API fails."""


def is_configured():
    return bool(
        GEMINI_API_KEY
        or GEMINI_API_KEY_2
    )


def get_configured_keys():
    keys = []

    if GEMINI_API_KEY:
        keys.append(
            {
                "name": "Gemini-1",
                "key": GEMINI_API_KEY,
                "model": GEMINI_MODEL,
                "url": GEMINI_URL,
            }
        )

    if GEMINI_API_KEY_2:
        keys.append(
            {
                "name": "Gemini-2",
                "key": GEMINI_API_KEY_2,
                "model": GEMINI_MODEL_2,
                "url": GEMINI_URL_2,
            }
        )

    return keys


def generate(
    prompt,
    temperature=None,
    max_output_tokens=None,
):
    configured_keys = get_configured_keys()

    if not configured_keys:
        raise GeminiError(
            "No Gemini API key is configured."
        )

    errors = []

    for config in configured_keys:
        try:
            return generate_with_key(
                prompt=prompt,
                api_key=config["key"],
                model=config["model"],
                url=config["url"],
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

        except Exception as error:
            errors.append(
                f'{config["name"]}: {error}'
            )

    raise GeminiError(
        "All Gemini keys failed.\n"
        + "\n".join(errors)
    )


def generate_with_key(
    prompt,
    api_key,
    model,
    url,
    temperature=None,
    max_output_tokens=None,
):
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
        f"{url}?key={api_key}",
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
        error_data = result["error"]

        if isinstance(error_data, dict):
            message = error_data.get(
                "message",
                "Gemini API error.",
            )
        else:
            message = str(error_data)

        raise GeminiError(message)

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
    configured_keys = get_configured_keys()

    models = [
        item["model"]
        for item in configured_keys
    ]

    return {
        "provider": "Gemini",
        "model": ", ".join(models),
        "configured": bool(
            configured_keys
        ),
        "key_count": len(
            configured_keys
        ),
    }
