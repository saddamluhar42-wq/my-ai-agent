"""Capability-aware model routing for Ultra Legend AI Core.

The router chooses a preferred provider without removing the existing fallback
chain. Explicit user/provider selection always wins; otherwise task signals
choose a suitable first model and the existing engine can fail over safely.
"""

from __future__ import annotations

import re
from typing import Optional

from ai.agent import get_available_providers


def classify_task(query: str, skill: str = "") -> str:
    text = f"{query} {skill}".lower()
    if re.search(r"\b(code|coding|python|javascript|typescript|debug|bug|repository|github|api|sql|program)\b", text):
        return "coding"
    if re.search(r"\b(research|paper|study|academic|scientific|source|citation|latest|current|news)\b", text):
        return "research"
    if re.search(r"\b(image|video|story|script|creative|thumbnail|prompt|animation|design)\b", text):
        return "creative"
    if re.search(r"\b(analyze|analysis|compare|strategy|architecture|plan|reason|complex)\b", text):
        return "reasoning"
    return "general"


def choose_provider(
    query: str,
    *,
    skill: str = "",
    explicit_provider: Optional[str] = None,
) -> tuple[Optional[str], str]:
    if explicit_provider:
        return explicit_provider, "explicit_user_selection"

    available = {name.lower(): name for name in get_available_providers()}
    task = classify_task(query, skill)

    preferences = {
        "coding": ("DeepSeek", "OpenAI", "Anthropic", "Gemini"),
        "research": ("Gemini", "Anthropic", "OpenAI", "DeepSeek"),
        "creative": ("Gemini", "OpenAI", "Anthropic", "Kimi"),
        "reasoning": ("Anthropic", "OpenAI", "Gemini", "DeepSeek"),
        "general": ("Gemini", "DeepSeek", "Anthropic", "Kimi", "OpenAI"),
    }
    for provider in preferences[task]:
        if provider.lower() in available:
            return available[provider.lower()], f"capability_route:{task}"
    return None, f"fallback_route:{task}"
