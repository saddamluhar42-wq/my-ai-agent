"""Lightweight capability router.

Routes a request to one capability only. Heavy intelligence remains external.
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
        "app_development": (
            "build an app", "build app", "create an app", "create app", "make an app",
            "make app", "develop an app", "develop app", "website", "web app",
            "mobile app", "android app", "ios app", "dashboard", "saas", "prototype",
            "replit", "deploy app", "publish app",
        ),
        "openai_developer": (
            "openai developer", "openai api", "openai sdk", "openai agents", "agents sdk",
            "openai platform", "openai key", "openai_api_key", "gpt api", "responses api",
            "chat completions", "openai integration", "build with openai",
        ),
        "outlook_calendar": (
            "calendar", "outlook calendar", "meeting", "meetings", "appointment", "appointments",
            "schedule", "scheduling", "event", "events", "free time", "availability",
            "reminder", "reschedule", "cancel meeting", "accept meeting", "decline meeting",
        ),
        "file_storage": (
            "dropbox", "cloud storage", "cloud file", "cloud files", "upload file", "upload files",
            "download file", "download files", "save to cloud", "save file to cloud",
            "list files", "find file", "find files", "share file", "share files",
        ),
        "coder": (
            "code", "coding", "python", "javascript", "typescript", "debug", "bug",
            "error", "refactor", "program", "script", "function", "class", "api", "sql",
        ),
        "web_search": (
            "search", "web", "internet", "latest", "today", "current", "news", "research",
            "source", "official", "price", "weather", "compare",
        ),
        "image_generator": (
            "image", "picture", "photo", "draw", "generate an image", "create image",
            "thumbnail", "visual",
        ),
        "memory": (
            "remember", "memory", "saved", "forgot", "recall", "what did i tell you",
        ),
        "documents": (
            "document", "pdf", "file", "uploaded", "attachment", "summarize this file",
        ),
    }

    def route(self, query: str, context: Mapping[str, Any] | None = None) -> Route:
        text = str(query or "").strip().lower()
        if not text:
            return Route("general", "empty request", 1.0)

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

        scores.sort(key=lambda item: (-item[0], item[1]))
        score, capability = scores[0]
        if len(scores) > 1 and scores[0][0] == scores[1][0]:
            return Route("general", "ambiguous capability; no plugin fan-out", 0.6)
        return Route(capability, f"matched {score} capability signal(s)", min(0.99, 0.7 + score * 0.1))

    def select(self, query: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        route = self.route(query, context)
        return {
            "capability": route.capability,
            "reason": route.reason,
            "confidence": route.confidence,
            "fan_out": False,
            "external_service": {
                "app_development": "Replit",
                "openai_developer": "OpenAI Platform",
                "outlook_calendar": "Microsoft Outlook Calendar",
                "file_storage": "Dropbox",
            }.get(route.capability),
        }


router = CapabilityRouter()
