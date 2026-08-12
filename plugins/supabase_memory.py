from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List
from urllib.parse import quote

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("SUPABASE_EMBEDDING_MODEL", "gemini-embedding-001").strip()
EMBEDDING_DIMENSIONS = 1536
TIMEOUT = max(3, min(int(os.getenv("SUPABASE_TIMEOUT", "8")), 20))
MAX_CONTENT = 6000
MIN_SIMILARITY = float(os.getenv("SUPABASE_MIN_SIMILARITY", "0.25"))


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _request(path: str, method: str = "GET", payload: Any = None) -> Any:
    if not is_configured():
        raise RuntimeError("Supabase plugin is not configured")
    if not path.startswith("/") or not SUPABASE_URL.startswith("https://"):
        raise RuntimeError("Invalid Supabase endpoint")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(SUPABASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Supabase HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Supabase network error") from exc


def _embed(text: str) -> List[float] | None:
    if not GEMINI_API_KEY or not text.strip():
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={quote(GEMINI_API_KEY, safe='')}"
    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text[:MAX_CONTENT]}]},
        "outputDimensionality": EMBEDDING_DIMENSIONS,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        values = data.get("embedding", {}).get("values") or []
        return [float(value) for value in values] if len(values) == EMBEDDING_DIMENSIONS else None
    except Exception:
        return None


def _usable(rows: Any, limit: int) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    result: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        similarity = row.get("similarity")
        if similarity is not None and float(similarity) < MIN_SIMILARITY:
            continue
        result.append(row)
        if len(result) >= limit:
            break
    return result


def remember(owner_key: str, content: str, metadata: Dict[str, Any] | None = None) -> bool:
    owner_key = str(owner_key or "").strip()[:200]
    content = str(content or "").strip()[:MAX_CONTENT]
    if not owner_key or not content or not is_configured():
        return False
    row: Dict[str, Any] = {"owner_key": owner_key, "content": content, "metadata": metadata or {}}
    embedding = _embed(content)
    if embedding:
        row["embedding"] = embedding
    try:
        _request("/rest/v1/memories", "POST", row)
        return True
    except Exception:
        return False


def recall(owner_key: str, query: str, limit: int = 6) -> List[Dict[str, Any]]:
    owner_key = str(owner_key or "").strip()[:200]
    query = str(query or "").strip()[:MAX_CONTENT]
    limit = max(1, min(int(limit), 10))
    if not owner_key or not query or not is_configured():
        return []
    embedding = _embed(query)
    if embedding:
        try:
            rows = _request("/rest/v1/rpc/match_memories", "POST", {"query_embedding": embedding, "match_owner_key": owner_key, "match_count": limit})
            return _usable(rows, limit)
        except Exception:
            pass
    params = f"?select=id,content,metadata,created_at&owner_key=eq.{quote(owner_key, safe='')}&order=created_at.desc&limit={limit}"
    try:
        return _usable(_request("/rest/v1/memories" + params), limit)
    except Exception:
        return []


def add_knowledge(owner_key: str, content: str, title: str = "", source: str = "", metadata: Dict[str, Any] | None = None) -> bool:
    owner_key = str(owner_key or "").strip()[:200]
    content = str(content or "").strip()[:MAX_CONTENT]
    if not owner_key or not content or not is_configured():
        return False
    row: Dict[str, Any] = {"owner_key": owner_key, "title": str(title or "")[:300], "content": content, "source": str(source or "")[:1000], "metadata": metadata or {}}
    embedding = _embed(content)
    if embedding:
        row["embedding"] = embedding
    try:
        _request("/rest/v1/knowledge", "POST", row)
        return True
    except Exception:
        return False


def search_knowledge(owner_key: str, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    return _vector_search("match_knowledge", owner_key, query, limit)


def add_document(owner_key: str, filename: str, content: str, mime_type: str = "", metadata: Dict[str, Any] | None = None) -> bool:
    owner_key = str(owner_key or "").strip()[:200]
    content = str(content or "").strip()[:MAX_CONTENT]
    if not owner_key or not filename or not content or not is_configured():
        return False
    row: Dict[str, Any] = {"owner_key": owner_key, "filename": str(filename)[:300], "mime_type": str(mime_type)[:200], "content": content, "metadata": metadata or {}}
    embedding = _embed(content)
    if embedding:
        row["embedding"] = embedding
    try:
        _request("/rest/v1/documents", "POST", row)
        return True
    except Exception:
        return False


def search_documents(owner_key: str, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    return _vector_search("match_documents", owner_key, query, limit)


def _vector_search(function: str, owner_key: str, query: str, limit: int) -> List[Dict[str, Any]]:
    owner_key = str(owner_key or "").strip()[:200]
    query = str(query or "").strip()[:MAX_CONTENT]
    limit = max(1, min(int(limit), 12))
    if not owner_key or not query or not is_configured():
        return []
    embedding = _embed(query)
    if not embedding:
        return []
    try:
        rows = _request(f"/rest/v1/rpc/{function}", "POST", {"query_embedding": embedding, "match_owner_key": owner_key, "match_count": limit})
        return _usable(rows, limit)
    except Exception:
        return []


def recall_context(owner_key: str, query: str, memory_limit: int = 5, knowledge_limit: int = 5, document_limit: int = 5) -> str:
    sections: List[str] = []
    memories = recall(owner_key, query, memory_limit)
    knowledge = search_knowledge(owner_key, query, knowledge_limit)
    documents = search_documents(owner_key, query, document_limit)
    if memories:
        sections.append("MEMORY:\n" + "\n".join(f"- {str(x.get('content') or '')[:1200]}" for x in memories))
    if knowledge:
        sections.append("KNOWLEDGE:\n" + "\n".join(f"- {str(x.get('title') or '').strip()}: {str(x.get('content') or '')[:1400]}" for x in knowledge))
    if documents:
        sections.append("DOCUMENTS:\n" + "\n".join(f"- {str(x.get('filename') or '')}: {str(x.get('content') or '')[:1400]}" for x in documents))
    return "\n\n".join(sections)


def memory_text(rows: List[Dict[str, Any]]) -> str:
    return "\n".join(f"- {str(row.get('content') or '').strip()[:1500]}" for row in rows[:10] if str(row.get('content') or '').strip())
