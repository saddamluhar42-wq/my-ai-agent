"""Single Render entrypoint for the Streamlit UI and OpenAI-compatible API."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from api.openai_compat import chat_completion
from api.server import ChatCompletionRequest, verify_key

STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_PORT = 8501
API_HOST = "127.0.0.1"
API_PORT = 8001


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
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
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


api_app = FastAPI(title="My AI Agent Internal API", version="1.0.0")
app = FastAPI(title="My AI Agent Gateway", version="1.0.0", lifespan=lifespan)


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


@api_app.post("/v1/chat/completions")
def completions(
    request: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    verify_key(authorization)
    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming is not supported yet.")
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty.")

    user_messages = [
        message.content.strip()
        for message in request.messages
        if message.role == "user" and message.content.strip()
    ]
    if not user_messages:
        raise HTTPException(status_code=400, detail="At least one user message is required.")

    result = chat_completion(user_messages[-1])
    result["model"] = request.model or "my-ai-agent"
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "my-ai-agent"}


@app.api_route(
    "/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def api_proxy(request: Request, path: str) -> Response:
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    target = f"http://{API_HOST}:{API_PORT}/v1/{path}"
    if request.url.query:
        target += f"?{request.url.query}"

    async with httpx.AsyncClient(follow_redirects=False) as client:
        upstream = await client.request(
            request.method,
            target,
            headers=headers,
            content=body,
            timeout=None,
        )

    excluded = {"content-length", "transfer-encoding", "connection"}
    response_headers = {
        key: value for key, value in upstream.headers.items() if key.lower() not in excluded
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


async def streamlit_http_proxy(request: Request) -> Response:
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    target = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}{request.url.path}"
    if request.url.query:
        target += f"?{request.url.query}"

    async with httpx.AsyncClient(follow_redirects=False) as client:
        upstream = await client.request(
            request.method,
            target,
            headers=headers,
            content=body,
            timeout=None,
        )

    excluded = {"content-length", "transfer-encoding", "connection"}
    response_headers = {
        key: value for key, value in upstream.headers.items() if key.lower() not in excluded
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def streamlit_proxy(request: Request, path: str) -> Response:
    return await streamlit_http_proxy(request)


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
