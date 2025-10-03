from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_202_ACCEPTED

from .config import get_settings
from .db import ensure_db_initialized, init_db
from .logging import RequestIdMiddleware, configure_logging
from .ratelimit import key_func_with_api_key, limiter
from .rpc import dispatch_jsonrpc
from .security import ApiKeyAuthMiddleware
from .sse import sse_manager


configure_logging()
app = FastAPI(title="MCP Telegram Server")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


# Middleware order: request_id -> API key -> rate limit -> routes
app.add_middleware(RequestIdMiddleware)
app.add_middleware(ApiKeyAuthMiddleware)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    settings = get_settings()
    # RATE_LIMIT format: "10/second" or "100/minute"
    try:
        count_str, per = settings.RATE_LIMIT.split("/")
        count = int(count_str)
        key = key_func_with_api_key(request)
        route_key = f"{key}:{request.url.path}"
        await limiter.hit(route_key, limit=count)
    except Exception:  # noqa: BLE001
        pass
    return await call_next(request)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/mcp/sse")
async def mcp_sse(request: Request) -> Any:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    client_id = request.query_params.get("client_id")
    return await sse_manager.subscribe(request, api_key, client_id)


@app.post("/mcp/rpc")
async def mcp_rpc(request: Request) -> JSONResponse:
    # Ensure DB exists even in test clients where startup didn't run
    await ensure_db_initialized()
    body = await request.json()
    sync = request.query_params.get("sync") == "true"
    api_key = request.headers.get("X-API-Key") or ""
    client_id = request.query_params.get("client_id")

    async def process_and_publish(payload: dict[str, Any]) -> dict[str, Any]:
        response = await dispatch_jsonrpc(request, payload)
        await sse_manager.publish(api_key, client_id, str(payload.get("id")), response)
        return response

    if sync:
        response = await process_and_publish(body)
        return JSONResponse(content=response)
    else:
        asyncio.create_task(process_and_publish(body))
        return JSONResponse(status_code=HTTP_202_ACCEPTED, content={"accepted": True, "id": body.get("id")})
