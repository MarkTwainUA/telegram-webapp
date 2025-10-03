from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from httpx import Response
from httpx._transports.mock import MockTransport

from app.main import app
from app.config import get_settings


settings = get_settings()


def make_transport():
    def handler(request: httpx.Request) -> Response:
        url = str(request.url)
        data = json.loads(request.content.decode() or "{}")
        if url.endswith("sendMessage"):
            result = {
                "message_id": 100,
                "date": 1700000000,
                "text": data.get("text"),
                "chat": {"id": -100123, "username": "chan"},
            }
            return Response(200, json={"ok": True, "result": result})
        if url.endswith("editMessageText"):
            result = {"message": {"message_id": data.get("message_id"), "date": 1700000100, "text": data.get("text"), "chat": {"id": -100123, "username": "chan"}}}
            return Response(200, json={"ok": True, "result": result})
        if url.endswith("deleteMessage"):
            return Response(200, json={"ok": True, "result": True})
        return Response(500)

    return MockTransport(handler)


@pytest.fixture(autouse=True)
def api_key_header():
    app.dependency_overrides = {}
    return {"X-API-Key": settings.API_KEY}


def test_tools_list(api_key_header):
    client = TestClient(app)
    payload = {"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}
    resp = client.post("/mcp/rpc?sync=true", headers=api_key_header, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["tools"][0]["name"] == "telegram.create_post"


def test_tools_call_create(api_key_header, monkeypatch):
    client = TestClient(app)

    # Patch TelegramClient to use MockTransport
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = make_transport()
        return original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    payload = {
        "jsonrpc": "2.0",
        "id": "abc-123",
        "method": "tools/call",
        "params": {
            "name": "telegram.create_post",
            "arguments": {"chat_id": "@chan", "text": "Hello"},
            "idempotency_key": "rpc-test-1"
        },
    }
    resp = client.post("/mcp/rpc?sync=true", headers=api_key_header, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "abc-123"
    assert data["result"]["message_id"] == 100
