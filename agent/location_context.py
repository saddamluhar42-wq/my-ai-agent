"""Location context detection for natural location-aware conversations."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen


_GENERIC = {
    "hi", "hello", "hey", "ok", "okay", "yes", "no", "haan", "ha", "haa",
    "done", "thanks", "thank", "bye", "weather", "news", "price", "time",
    "today", "tomorrow", "help", "please", "what", "why", "how", "who", "where",
}


def _clean(text: str) -> str:
    text = re.sub(r"[^\w\s&'-]", " ", str(text or ""), flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _candidates(text: str) -> list[str]:
    clean = _clean(text)
    if not clean:
        return []
    words = clean.split()
    candidates: list[str] = []

    # Explicit location phrases: "in Mumbai", "Mumbai me", "at Delhi".
    patterns = [
        r"\b(?:in|at|near|from|to)\s+([A-Za-z][A-Za-z .'-]{1,60})$",
        r"\b([A-Za-z][A-Za-z .'-]{1,60})\s+(?:me|mein|ka|ki|ke|weather|news|temperature|traffic)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, re.I)
        if match:
            value = match.group(1).strip(" .,-")
            if value and value.lower() not in _GENERIC:
                candidates.append(value)

    # Short whole-message location names, e.g. "Mumbai" or "New Delhi".
    if len(words) <= 4 and all(w.lower() not in _GENERIC for w in words):
        candidates.append(clean)

    # Try short n-grams so "Mumbai ka weather" can resolve Mumbai.
    for size in (3, 2, 1):
        for i in range(max(0, len(words) - size + 1)):
            value = " ".join(words[i:i + size]).strip()
            if value and value.lower() not in _GENERIC and len(value) >= 3:
                candidates.append(value)

    # Preserve order and remove duplicates.
    seen = set()
    return [c for c in candidates if not (c.lower() in seen or seen.add(c.lower()))]


def _geocode(candidate: str) -> Optional[Dict[str, Any]]:
    """Resolve a human place name using OpenStreetMap Nominatim."""
    url = (
        "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&q="
        + quote(candidate)
    )
    try:
        request = Request(
            url,
            headers={
                "User-Agent": "My-AI-Agent/1.0 location-context",
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=3.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data:
            return None
        item = data[0]
        return {
            "query": candidate,
            "display_name": item.get("display_name", candidate),
            "latitude": item.get("lat"),
            "longitude": item.get("lon"),
            "type": item.get("type", ""),
            "address": item.get("address", {}),
        }
    except Exception:
        return None


def _user_messages(recent_messages: Iterable[Any]) -> list[str]:
    values = []
    for message in recent_messages or []:
        if not isinstance(message, dict):
            continue
        if str(message.get("role", "")).lower() != "user":
            continue
        content = str(message.get("content", "") or "").strip()
        if content:
            values.append(content)
    return values


def resolve_location(query: str, recent_messages: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    """Find an explicit location in the current query or recent user context."""
    sources = [str(query or "").strip()]
    sources.extend(reversed(_user_messages(recent_messages)))

    checked = set()
    for source_index, source in enumerate(sources):
        for candidate in _candidates(source):
            key = candidate.lower()
            if key in checked:
                continue
            checked.add(key)
            result = _geocode(candidate)
            if result:
                result["source"] = "current_query" if source_index == 0 else "conversation_context"
                return result
    return None


def format_location_context(location: Optional[Dict[str, Any]]) -> str:
    if not location:
        return ""
    address = location.get("address") or {}
    parts = [
        address.get("city") or address.get("town") or address.get("village") or address.get("municipality"),
        address.get("state"),
        address.get("country"),
    ]
    parts = [str(p) for p in parts if p]
    canonical = ", ".join(dict.fromkeys(parts))
    return (
        f"Active location: {location.get('display_name', '')}\n"
        f"Canonical location: {canonical or location.get('display_name', '')}\n"
        f"Coordinates: {location.get('latitude', '')}, {location.get('longitude', '')}\n"
        "Use this location for location-dependent follow-up questions such as weather, news, traffic, time, events, and other current information."
    )
