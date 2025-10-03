from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Tuple

from fastapi import Request
from starlette.responses import StreamingResponse


class SSEManager:
    def __init__(self) -> None:
        # Map subscriber key to a queue of (event_id, data_json)
        self._subscribers: dict[str, "asyncio.Queue[Tuple[str, str]]"] = {}

    def _key(self, api_key: str, client_id: str | None) -> str:
        return f"{api_key}:{client_id or 'default'}"

    async def subscribe(self, request: Request, api_key: str, client_id: str | None) -> StreamingResponse:
        queue: asyncio.Queue[Tuple[str, str]] = asyncio.Queue()
        key = self._key(api_key, client_id)
        self._subscribers[key] = queue

        async def event_generator():
            try:
                # initial comment to establish
                yield b": connected\n\n"
                while True:
                    try:
                        event_id, item = await asyncio.wait_for(queue.get(), timeout=15)
                        # Use the correlated JSON-RPC id as the SSE id
                        yield f"event: message\nid: {event_id}\ndata: {item}\n\n".encode()
                    except asyncio.TimeoutError:
                        yield b": keep-alive\n\n"
                    if await request.is_disconnected():
                        break
            finally:
                self._subscribers.pop(key, None)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    async def publish(self, api_key: str, client_id: str | None, request_id: str, payload: Dict[str, Any]) -> None:
        key = self._key(api_key, client_id)
        data = json.dumps(payload, separators=(",", ":"))
        queue = self._subscribers.get(key)
        if queue:
            await queue.put((request_id, data))


sse_manager = SSEManager()
