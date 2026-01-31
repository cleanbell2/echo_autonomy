"""
Test health endpoint — Phase 4
"""

import pytest
from fastapi.testclient import TestClient

from echo_gateway.server.app import create_app


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health_returns_ok(client):
    """Health endpoint returns 200 + ok:true."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["service"] == "echo_gateway"
    assert data["phase"] == 4
