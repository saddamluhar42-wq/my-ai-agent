"""OpenAI-compatible API adapter for My AI Agent."""

from __future__ import annotations

from typing import Any


def chat_completion(
    query: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the existing agent with bounded conversation context."""
    from agent.core import run_agent

    safe_context = dict(context or {})
    recent = safe_context.get("recent_messages", [])
    if isinstance(recent, list):
        safe_context["recent_messages"] = [
            {"role": str(item.get("role", "")), "content": str(item.get("content", ""))[:12000]}
            for item in recent[-20:]
            if isinstance(item, dict) and str(item.get("content", "")).strip()
        ]
    else:
        safe_context["recent_messages"] = []

    result = run_agent(query=query, context=safe_context)

    if not result.success:
        error = (result.metadata or {}).get("error", "Agent execution failed.")
        raise RuntimeError(error)

    metadata = result.metadata or {}
    model = metadata.get("model") or "my-ai-agent"

    return {
        "id": "chatcmpl-my-ai-agent",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.answer or "",
                },
                "finish_reason": "stop",
            }
        ],
    }
