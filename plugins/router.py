"""Lightweight capability router.

Routes a request to one capability only. It does not implement heavy
intelligence and never executes plugins itself; callers resolve the selected
capability through the external plugin manager.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Route:
    capability: str
    reason: str
    confidence: float


class CapabilityRouter:
    """Fast deterministic first-pass router with no model/network call."""

    RULES = {
        "coder": ("code", "coding", "python", "javascript", "typescript", "debug", "bug", "error", "refactor", "program", "script", "function", "class", "api", "sql"),
        "web_search": ("search", "web", "internet", "latest", "today", "current", "news", "research", "source", "official", "price", "weather", "compare"),
        "image_generator": ("image", "picture", "photo", "draw", "generate an image", "create image", "thumbnail", "visual"),
        "memory": ("remember", "memory", "saved", "forgot", "recall", "what did i tell you"),
        "documents": ("document", "pdf", "file", "uploaded", "attachment", "summarize this file"),
    }

    def route(self, query: str, context: Mapping[str, Any] | None = None) -> Route:
        text = str(query or "").strip().lower()
        if not text:
            return Route("general", "empty request", 1.0)

        # Explicit context has priority and avoids unnecessary intent guessing.
        requested = str((context or {}).get("capability") or "").strip().lower()
        if requested in self.RULES or requested == "general":
            return Route(requested, "explicit capability", 1.0)

        scores = []
        for capability, terms in self.RULES.items():
            score = sum(1 for term in terms if term in text)
            if score:
                scores.append((score, capability))
        if not scores:
            return Route("general", "no specialized capability matched", 0.95)

        scores.sort(reverse=True)
        score, capability = scores[0]
        # Ambiguous requests stay general rather than calling multiple plugins.
        if len(scores) > 1 and scores[0][0] == scores[1][0]:
            return Route("general", "ambiguous capability; no plugin fan-out", 0.6)
        return Route(capability, f"matched {score} capability signal(s)", min(0.99, 0.7 + score * 0.1))

    def select(self, query: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        route = self.route(query, context)
        return {"capability": route.capability, "reason": route.reason, "confidence": route.confidence, "fan_out": False}


router = CapabilityRouter()
