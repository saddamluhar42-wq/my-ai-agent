"""OpenAI-compatible HTTP API for My AI Agent.

Deploy this module as a separate Render Web Service so the existing Streamlit
UI remains untouched. Set API_ACCESS_KEY in Render environment variables.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api.openai_compat import chat_completion

app = FastAPI(title="My AI Agent API", version="1.0.0")


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


@app.post("/v1/chat/completions")
def completions(
    request: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    verify_key(authorization)

    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming is not supported yet.")

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty.")

    user_messages = [m.content.strip() for m in request.messages if m.role == "user" and m.content.strip()]
    if not user_messages:
        raise HTTPException(status_code=400, detail="At least one user message is required.")

    query = user_messages[-1]
    result = chat_completion(query)
    result["model"] = request.model or "my-ai-agent"
    return result
