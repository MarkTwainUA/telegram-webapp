from __future__ import annotations

import json
import time
from threading import Thread

from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


settings = get_settings()


def test_sse_subscribe_and_publish():
    client = TestClient(app)

    with client.stream("GET", "/mcp/sse", headers={"X-API-Key": settings.API_KEY}) as s:
        # send an RPC that will stream back
        payload = {"jsonrpc": "2.0", "id": "evt-1", "method": "tools/list", "params": {}}
        r = client.post("/mcp/rpc", headers={"X-API-Key": settings.API_KEY}, json=payload)
        assert r.status_code == 202
        # read a few chunks until we find data:
        found = False
        for line in s.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
                assert data["id"] == "evt-1"
                found = True
                break
        assert found
