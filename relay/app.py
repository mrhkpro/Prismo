import os
from typing import Dict

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "").strip().rstrip("/")
UPSTREAM_API_KEY = os.getenv("UPSTREAM_API_KEY", "").strip()
RELAY_API_KEY = os.getenv("RELAY_API_KEY", "").strip()
CONNECT_TIMEOUT = float(os.getenv("RELAY_CONNECT_TIMEOUT", "20"))
READ_TIMEOUT = float(os.getenv("RELAY_READ_TIMEOUT", "180"))

app = FastAPI(title="Prismo AI Relay")


def _auth_ok(request: Request) -> bool:
    if not RELAY_API_KEY:
        return True
    return request.headers.get("authorization", "") == f"Bearer {RELAY_API_KEY}"


def _forward_headers(request: Request) -> Dict[str, str]:
    headers = {}
    for key, value in request.headers.items():
        lower = key.lower()
        if lower in {"host", "content-length", "connection"}:
            continue
        headers[key] = value
    if UPSTREAM_API_KEY:
        headers["authorization"] = f"Bearer {UPSTREAM_API_KEY}"
    return headers


@app.get("/health")
async def health():
    return {"ok": bool(UPSTREAM_BASE_URL), "upstream_configured": bool(UPSTREAM_BASE_URL)}


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    if not UPSTREAM_BASE_URL:
        return Response("UPSTREAM_BASE_URL is not configured.", status_code=503, media_type="text/plain")
    if not _auth_ok(request):
        return Response("Unauthorized relay request.", status_code=401, media_type="text/plain")

    upstream_url = f"{UPSTREAM_BASE_URL}/" + path.lstrip("/")
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    body = await request.body()
    timeout = httpx.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            upstream = await client.request(
                request.method,
                upstream_url,
                content=body,
                headers=_forward_headers(request),
            )
    except httpx.ConnectTimeout:
        return Response("Relay could not connect to upstream in time.", status_code=504, media_type="text/plain")
    except httpx.TimeoutException:
        return Response("Relay upstream request timed out.", status_code=504, media_type="text/plain")
    except httpx.RequestError as exc:
        return Response(f"Relay upstream connection failed: {type(exc).__name__}", status_code=502, media_type="text/plain")

    excluded = {"content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in upstream.headers.items() if k.lower() not in excluded}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
