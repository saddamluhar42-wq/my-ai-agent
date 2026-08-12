from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("SUPABASE_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSIONS = 1536
TIMEOUT = 8
MAX_CONTENT = 6000


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _request(path: str, method: str = "GET", payload: Any = None) -> Any:
    if not is_configured():
        raise RuntimeError("Supabase plugin is not configured.")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(SUPABASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:300]
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase network error: {exc.reason}") from exc


def _embed(text: str) -> List[float] | None:
    if not GEMINI_API_KEY or not text.strip():
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text[:MAX_CONTENT]}]},
        "outputDimensionality": EMBEDDING_DIMENSIONS,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        values = data.get("embedding", {}).get("values") or []
        return [float(value) for value in values] if len(values) == EMBEDDING_DIMENSIONS else None
    except Exception:
        return None


def remember(owner_key: str, content: str, metadata: Dict[str, Any] | None = None) -> bool:
    owner_key = str(owner_key or "").strip()
    content = str(content or "").strip()
    if not owner_key or not content or not is_configured():
        return False
    content = content[:MAX_CONTENT]
    embedding = _embed(content)
    row: Dict[str, Any] = {
        "owner_key": owner_key[:200],
        "content": content,
        "metadata": metadata or {},
    }
    if embedding:
        row["embedding"] = embedding
    try:
        _request("/rest/v1/memories", method="POST", payload=row)
        return True
    except Exception:
        return False


def recall(owner_key: str, query: str, limit: int = 6) -> List[Dict[str, Any]]:
    owner_key = str(owner_key or "").strip()
    query = str(query or "").strip()
    if not owner_key or not query or not is_configured():
        return []
    limit = max(1, min(int(limit), 10))
    embedding = _embed(query)
    if embedding:
        try:
            result = _request(
                "/rest/v1/rpc/match_memories",
                method="POST",
                payload={"query_embedding": embedding, "match_owner_key": owner_key[:200], "match_count": limit},
            )
            return result if isinstance(result, list) else []
        except Exception:
            pass

    from urllib.parse import quote
    params = (
        f"?select=id,content,metadata,created_at"
        f"&owner_key=eq.{quote(owner_key[:200], safe='')}"
        f"&content=ilike.*{quote(query[:80], safe='')}*"
        f"&order=created_at.desc&limit={limit}"
    )
    try:
        result = _request("/rest/v1/memories" + params)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def memory_text(rows: List[Dict[str, Any]]) -> str:
    parts = []
    for row in rows[:10]:
        text = str(row.get("content") or "").strip()
        if text:
            parts.append("- " + text[:1500])
    return "\n".join(parts)
