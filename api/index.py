import asyncio
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import websockets
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_ENTRYPOINT = os.getenv("STREAMLIT_ENTRYPOINT", "main.py")
STREAMLIT_INTERNAL_PORT = int(os.getenv("STREAMLIT_INTERNAL_PORT", "8501"))
STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_BOOT_TIMEOUT_SECONDS = float(os.getenv("STREAMLIT_BOOT_TIMEOUT_SECONDS", "30"))

_streamlit_process: subprocess.Popen | None = None
_streamlit_lock = threading.Lock()


def _build_streamlit_command() -> list[str]:
    entrypoint = PROJECT_ROOT / STREAMLIT_ENTRYPOINT
    if not entrypoint.exists():
        raise RuntimeError(
            f"Configured Streamlit entrypoint not found: {entrypoint}"
        )

    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        STREAMLIT_ENTRYPOINT,
        "--server.address",
        STREAMLIT_HOST,
        "--server.port",
        str(STREAMLIT_INTERNAL_PORT),
        "--server.headless",
        "true",
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
        "--client.showErrorDetails",
        "false",
        "--client.toolbarMode",
        "minimal",
    ]


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _wait_for_streamlit_startup() -> None:
    deadline = time.time() + STREAMLIT_BOOT_TIMEOUT_SECONDS
    while time.time() < deadline:
        if _streamlit_process is not None and _streamlit_process.poll() is not None:
            raise RuntimeError("Streamlit process terminated during startup.")
        if _is_port_open(STREAMLIT_HOST, STREAMLIT_INTERNAL_PORT):
            return
        time.sleep(0.2)
    raise RuntimeError("Timed out waiting for Streamlit to become ready.")


def ensure_streamlit_running() -> None:
    global _streamlit_process

    if _is_port_open(STREAMLIT_HOST, STREAMLIT_INTERNAL_PORT):
        return

    with _streamlit_lock:
        if _is_port_open(STREAMLIT_HOST, STREAMLIT_INTERNAL_PORT):
            return

        if _streamlit_process is not None and _streamlit_process.poll() is None:
            _wait_for_streamlit_startup()
            return

        _streamlit_process = subprocess.Popen(
            _build_streamlit_command(),
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _wait_for_streamlit_startup()


def _forward_request_headers(request: Request) -> dict[str, str]:
    disallowed = {"host", "connection", "content-length", "transfer-encoding"}
    return {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in disallowed
    }


def _forward_response_headers(headers: httpx.Headers) -> dict[str, str]:
    disallowed = {"content-encoding", "transfer-encoding", "connection"}
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in disallowed
    }


async def proxy_http(request: Request) -> Response:
    try:
        ensure_streamlit_running()
    except RuntimeError as error:
        return PlainTextResponse(
            f"Failed to boot Streamlit runtime: {error}",
            status_code=500,
        )

    target_url = (
        f"http://{STREAMLIT_HOST}:{STREAMLIT_INTERNAL_PORT}"
        f"{request.url.path}"
    )
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    body = await request.body()
    async with httpx.AsyncClient(follow_redirects=False, timeout=60) as client:
        try:
            upstream_response = await client.request(
                request.method,
                target_url,
                content=body,
                headers=_forward_request_headers(request),
            )
        except httpx.RequestError as error:
            return PlainTextResponse(
                f"Failed to proxy request to Streamlit runtime: {error}",
                status_code=502,
            )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=_forward_response_headers(upstream_response.headers),
    )


def _websocket_headers(websocket: WebSocket) -> dict[str, str]:
    disallowed = {
        "host",
        "connection",
        "upgrade",
        "sec-websocket-key",
        "sec-websocket-version",
        "sec-websocket-extensions",
    }
    return {
        key: value
        for key, value in websocket.headers.items()
        if key.lower() not in disallowed
    }


async def proxy_websocket(websocket: WebSocket) -> None:
    try:
        ensure_streamlit_running()
    except RuntimeError:
        await websocket.close(code=1011)
        return

    await websocket.accept()
    target_url = (
        f"ws://{STREAMLIT_HOST}:{STREAMLIT_INTERNAL_PORT}"
        f"{websocket.url.path}"
    )
    if websocket.url.query:
        target_url = f"{target_url}?{websocket.url.query}"

    async with websockets.connect(
        target_url,
        additional_headers=_websocket_headers(websocket),
    ) as upstream:
        async def client_to_upstream() -> None:
            try:
                while True:
                    event = await websocket.receive()
                    event_type = event.get("type")
                    if event_type == "websocket.disconnect":
                        await upstream.close()
                        return
                    if event_type != "websocket.receive":
                        continue
                    if event.get("text") is not None:
                        await upstream.send(event["text"])
                        continue
                    if event.get("bytes") is not None:
                        await upstream.send(event["bytes"])
            except WebSocketDisconnect:
                await upstream.close()
            except websockets.ConnectionClosed:
                return

        async def upstream_to_client() -> None:
            try:
                while True:
                    message = await upstream.recv()
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                        continue
                    await websocket.send_text(message)
            except websockets.ConnectionClosed:
                await websocket.close()
            except RuntimeError:
                return

        receive_task = asyncio.create_task(client_to_upstream())
        send_task = asyncio.create_task(upstream_to_client())
        done, pending = await asyncio.wait(
            {receive_task, send_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in done:
            task.result()


async def healthcheck(_: Request) -> Response:
    return PlainTextResponse("ok", status_code=200)


app = Starlette(
    routes=[
        Route("/healthz", healthcheck, methods=["GET"]),
        WebSocketRoute("/{path:path}", proxy_websocket),
        Route("/{path:path}", proxy_http, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]),
    ]
)
