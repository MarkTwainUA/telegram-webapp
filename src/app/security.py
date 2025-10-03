from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from .config import get_settings


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path.startswith("/mcp/"):
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key != get_settings().API_KEY:
                return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"detail": "Unauthorized"})
        return await call_next(request)


def ensure_chat_allowed(chat_id: str | int) -> None:
    settings = get_settings()
    allowed = settings.allowed_chat_ids()
    if "*" in allowed:
        return
    value = str(chat_id)
    if value not in allowed:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="chat_id not allowed")
