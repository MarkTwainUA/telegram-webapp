from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


def test_readme_examples():
    client = TestClient(app)
    settings = get_settings()
    # health
    assert client.get("/healthz").json() == {"status": "ok"}
    # tools/list sync
    payload = {"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}
    resp = client.post("/mcp/rpc?sync=true", headers={"X-API-Key": settings.API_KEY}, json=payload)
    assert resp.status_code == 200
    assert any(t["name"].startswith("telegram.") for t in resp.json()["result"]["tools"])