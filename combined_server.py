"""Single Render entrypoint for the Streamlit UI and OpenAI-compatible API."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse
from api.openai_compat import chat_completion
from api.server import ChatCompletionRequest, verify_key

STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_PORT = 8501
API_HOST = "127.0.0.1"
API_PORT = 8001
PROXY_TIMEOUT_SECONDS = float(os.getenv("PROXY_TIMEOUT_SECONDS", "120"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    streamlit = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.address={STREAMLIT_HOST}",
            f"--server.port={STREAMLIT_PORT}",
            "--server.headless=true",
            "--server.enableCORS=true",
            "--server.enableXsrfProtection=true",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    api_config = uvicorn.Config(api_app, host=API_HOST, port=API_PORT, log_level="info")
    api_server = uvicorn.Server(api_config)
    api_task = asyncio.create_task(api_server.serve())

    try:
        for _ in range(60):
            if streamlit.poll() is not None:
                raise RuntimeError("Streamlit process exited during startup.")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}/_stcore/health",
                        timeout=1.0,
                    )
                    if response.status_code == 200:
                        break
            except Exception:
                pass
            await asyncio.sleep(0.5)
        yield
    finally:
        api_server.should_exit = True
        await api_task
        if streamlit.poll() is None:
            streamlit.send_signal(signal.SIGTERM)
            try:
                streamlit.wait(timeout=10)
            except subprocess.TimeoutExpired:
                streamlit.kill()


api_app = FastAPI(title="My AI Agent Internal API", version="1.1.0")
app = FastAPI(title="My AI Agent Gateway", version="1.1.0", lifespan=lifespan)


@api_app.get("/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": "my-ai-agent-api"}


@api_app.get("/v1/models")
def models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    verify_key(authorization)
    return {
        "object": "list",
        "data": [{"id": "my-ai-agent", "object": "model", "owned_by": "my-ai-agent"}],
    }


def _stream_response(result: dict[str, Any]) -> AsyncIterator[str]:
    async def generator() -> AsyncIterator[str]:
        choice = result["choices"][0]
        content = choice["message"].get("content", "") or ""
        model = result.get("model", "my-ai-agent")
        response_id = result.get("id", "chatcmpl-my-ai-agent")
        first = {
            "id": response_id, "object": "chat.completion.chunk", "created": 0, "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"
        for index in range(0, len(content), 120):
            chunk = {
                "id": response_id, "object": "chat.completion.chunk", "created": 0, "model": model,
                "choices": [{"index": 0, "delta": {"content": content[index:index + 120]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        final = {
            "id": response_id, "object": "chat.completion.chunk", "created": 0, "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    return generator()


@api_app.post("/v1/chat/completions")
def completions(
    request: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
):
    verify_key(authorization)
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty.")
    messages = [
        {"role": m.role, "content": m.content.strip()[:12000]}
        for m in request.messages[-20:]
        if m.content.strip()
    ]
    user_messages = [m["content"] for m in messages if m["role"] == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="At least one user message is required.")
    try:
        result = chat_completion(user_messages[-1], context={"recent_messages": messages[:-1]})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    result["model"] = request.model or "my-ai-agent"
    if request.stream:
        return StreamingResponse(
            _stream_response(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "my-ai-agent"}


async def _proxy_stream(request: Request, target: str) -> StreamingResponse:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
    body = await request.body()
    client = httpx.AsyncClient(follow_redirects=False, timeout=PROXY_TIMEOUT_SECONDS)
    try:
        upstream_request = client.build_request(request.method, target, headers=headers, content=body)
        upstream = await client.send(upstream_request, stream=True)
    except Exception:
        await client.aclose()
        raise

    excluded = {"content-length", "transfer-encoding", "connection"}
    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in excluded}

    async def iterator():
        try:
            async for chunk in upstream.aiter_bytes():
                if chunk:
                    yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        iterator(),
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def api_proxy(request: Request, path: str) -> StreamingResponse:
    target = f"http://{API_HOST}:{API_PORT}/v1/{path}"
    if request.url.query:
        target += f"?{request.url.query}"
    return await _proxy_stream(request, target)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def streamlit_proxy(request: Request, path: str) -> StreamingResponse:
    target = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}{request.url.path}"
    if request.url.query:
        target += f"?{request.url.query}"
    return await _proxy_stream(request, target)


@app.websocket("/{path:path}")
async def streamlit_websocket(websocket: WebSocket, path: str) -> None:
    from websockets.asyncio.client import connect

    await websocket.accept()
    target = f"ws://{STREAMLIT_HOST}:{STREAMLIT_PORT}/{path}"
    if websocket.query_params:
        target += "?" + str(websocket.query_params)
    try:
        async with connect(target, max_size=None) as upstream:
            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        break
                    if message.get("text") is not None:
                        await upstream.send(message["text"])
                    elif message.get("bytes") is not None:
                        await upstream.send(message["bytes"])

            async def upstream_to_client() -> None:
                async for message in upstream:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_text(message)

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
