"""OpenAI-compatible HTTP API for My AI Agent."""

from __future__ import annotations

import json
import os
import secrets
from typing import Any, Iterator

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.openai_compat import chat_completion

app = FastAPI(title="My AI Agent API", version="1.1.0")


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "my-ai-agent"
    messages: list[ChatMessage] = Field(default_factory=list)
    temperature: float | None = None
    stream: bool = False


def verify_key(authorization: str | None) -> None:
    expected = os.getenv("API_ACCESS_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="API_ACCESS_KEY is not configured.")

    supplied = (authorization or "").strip()
    if supplied.lower().startswith("bearer "):
        supplied = supplied[7:].strip()

    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid API key.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "my-ai-agent-api"}


@app.get("/v1/models")
def models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    verify_key(authorization)
    return {
        "object": "list",
        "data": [
            {
                "id": "my-ai-agent",
                "object": "model",
                "owned_by": "my-ai-agent",
            }
        ],
    }


def _stream_response(result: dict[str, Any]) -> Iterator[str]:
    """Return an OpenAI-compatible SSE stream from the completed agent answer.

    The agent itself currently produces a complete answer rather than token-level
    streaming. We therefore send that answer as one streamed content chunk so
    clients that require stream=true, such as Airgap, can consume it correctly.
    """
    choice = result.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = message.get("content", "") or ""
    model = result.get("model", "my-ai-agent")
    completion_id = result.get("id", "chatcmpl-my-ai-agent")

    first_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"

    if content:
        content_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(content_chunk, ensure_ascii=False)}\n\n"

    final_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
def completions(
    request: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any] | StreamingResponse:
    verify_key(authorization)

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty.")

    user_messages = [
        m.content.strip()
        for m in request.messages
        if m.role == "user" and m.content.strip()
    ]
    if not user_messages:
        raise HTTPException(status_code=400, detail="At least one user message is required.")

    query = user_messages[-1]
    result = chat_completion(query)
    result["model"] = request.model or "my-ai-agent"

    if request.stream:
        return StreamingResponse(
            _stream_response(result),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return result
