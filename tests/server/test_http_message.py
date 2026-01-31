"""
Test HTTP /api/message endpoint — Phase 4
"""

import time

import pytest
from fastapi.testclient import TestClient

from echo_gateway.server.app import create_app


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_api_message_happy_path(client):
    """POST /api/message with valid MessageRequest envelope."""
    envelope = {
        "session_id": "test-session",
        "timestamp": time.time(),
        "payload": {
            "type": "message",
            "content": "Hello gateway",
            "metadata": {"key": "value"},
        },
    }
    resp = client.post("/api/message", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "echo" in data["data"]
    assert data["data"]["echo"] == "Hello gateway"


def test_api_message_tool_call(client):
    """POST /api/message with ToolCallRequest envelope."""
    envelope = {
        "session_id": "tool-session",
        "timestamp": time.time(),
        "payload": {
            "type": "tool_call",
            "tool_name": "calculator",
            "arguments": {"op": "add", "a": 1, "b": 2},
        },
    }
    resp = client.post("/api/message", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["tool_name"] == "calculator"


def test_api_message_invalid_envelope(client):
    """POST /api/message with invalid envelope → error."""
    envelope = {
        "session_id": "bad-session",
        "timestamp": 0,  # too old
        "payload": {"type": "message", "content": "test"},
    }
    resp = client.post("/api/message", json=envelope)
    assert resp.status_code == 200  # gateway returns 200 with error in body
    data = resp.json()
    assert data["status"] == "error"
    assert "error" in data


def test_api_message_unknown_request_type(client):
    """POST /api/message with unknown request type → error."""
    envelope = {
        "session_id": "test-session",
        "timestamp": time.time(),
        "payload": {"type": "unknown_type"},
    }
    resp = client.post("/api/message", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert "error" in data
