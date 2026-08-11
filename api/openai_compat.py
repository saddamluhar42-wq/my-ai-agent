"""OpenAI-compatible API adapter for My AI Agent.

This module is intentionally framework-agnostic. The web service can import
`chat_completion` from its HTTP route and return the resulting dictionary as
JSON. It keeps the mobile client contract compatible with OpenAI clients.
"""

from __future__ import annotations

from typing import Any


def chat_completion(
    query: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the existing agent and return an OpenAI-compatible response."""
    from agent.core import run_agent

    result = run_agent(query=query, context=context or {})

    if not result.success:
        error = result.metadata.get("error", "Agent execution failed.")
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
