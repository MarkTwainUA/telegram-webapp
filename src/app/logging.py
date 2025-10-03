from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Optional

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


def _json_renderer(logger: Any, name: str, event_dict: Dict[str, Any]) -> str:
    return json.dumps(event_dict, separators=(",", ":"))


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", key="ts"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _json_renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(20),
        cache_logger_on_first_use=True,
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            structlog.get_logger().info(
                "request_complete",
                path=str(request.url),
                method=request.method,
                status_code=getattr(getattr(response, "__dict__", {}), "status_code", None),
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-Id"] = request_id
        return response
