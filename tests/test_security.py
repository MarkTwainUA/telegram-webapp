from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_auth_required():
    client = TestClient(app)
    resp = client.get("/mcp/sse")
    assert resp.status_code == 401


def test_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
