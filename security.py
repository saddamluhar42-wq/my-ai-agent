"""Small security helpers for provider/API boundaries.

Secrets are read from the environment only. This module never logs or returns
secret values and centralizes validation/redaction for model, image and search
providers.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

MAX_PROMPT_CHARS = int(os.getenv("SECURITY_MAX_PROMPT_CHARS", "12000"))
MAX_QUERY_CHARS = int(os.getenv("SECURITY_MAX_QUERY_CHARS", "2500"))
DEFAULT_TIMEOUT = float(os.getenv("SECURITY_REQUEST_TIMEOUT", "30"))


def secret(name: str) -> str | None:
    """Read a secret without ever exposing it through this module."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def require_https(url: str) -> str:
    """Allow only HTTPS provider endpoints."""
    if not isinstance(url, str) or not url.lower().startswith("https://"):
        raise ValueError("Provider endpoint must use HTTPS")
    return url


def clean_text(value: str, limit: int) -> str:
    """Normalize untrusted text and enforce a hard size limit."""
    if not isinstance(value, str):
        raise TypeError("Expected text input")
    value = value.replace("\x00", "").strip()
    if len(value) > limit:
        raise ValueError(f"Input exceeds the {limit}-character security limit")
    return value


def clean_prompt(prompt: str) -> str:
    return clean_text(prompt, MAX_PROMPT_CHARS)


def clean_search_query(query: str) -> str:
    return clean_text(query, MAX_QUERY_CHARS)


def safe_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return headers suitable for diagnostics with credential values redacted."""
    secret_headers = {"authorization", "x-api-key", "api-key", "x-goog-api-key"}
    return {
        key: ("[REDACTED]" if key.lower() in secret_headers else value)
        for key, value in headers.items()
    }


def redact_secrets(text: str, secrets: Iterable[str | None]) -> str:
    """Remove known secret values from error/log text."""
    result = str(text)
    for value in secrets:
        if value:
            result = result.replace(value, "[REDACTED]")
    # Also hide common API-key-shaped strings accidentally included in errors.
    result = re.sub(r"(?i)(api[_-]?key|token|authorization)(\s*[:=]\s*)\S+", r"\1\2[REDACTED]", result)
    return result
