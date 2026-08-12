"""Lightweight semantic embedding provider for the Universal Knowledge Hub.

Uses Gemini's embedding endpoint when a Gemini key is configured. The storage
layer keeps embeddings as JSON so the feature does not require a PostgreSQL
vector extension. Retrieval can therefore degrade gracefully to lexical search.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import List, Optional

from config import GEMINI_API_KEY, GEMINI_API_KEY_2, REQUEST_TIMEOUT

DEFAULT_EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:embedContent?key={key}"
)


def _keys() -> List[str]:
    return [key for key in (GEMINI_API_KEY, GEMINI_API_KEY_2) if key]


def embed_text(text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> Optional[List[float]]:
    """Return a normalized embedding, or None when embeddings are unavailable."""
    text = str(text or "").strip()
    if not text:
        return None

    payload = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": text[:12000]}]},
    }

    last_error = None
    for key in _keys():
        try:
            url = EMBEDDING_ENDPOINT.format(model=model, key=key)
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            values = data.get("embedding", {}).get("values", [])
            if not values:
                raise RuntimeError("Embedding API returned no vector.")
            vector = [float(value) for value in values]
            norm = sum(value * value for value in vector) ** 0.5
            return [value / norm for value in vector] if norm else vector
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, RuntimeError, OSError) as error:
            last_error = error

    return None


def embedding_available() -> bool:
    return bool(_keys())
