"""
Test WebSocket /ws endpoint — Phase 4
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


def test_ws_message_happy_path(client):
    """WebSocket /ws with valid MessageRequest envelope."""
    with client.websocket_connect("/ws") as ws:
        envelope = {
            "session_id": "ws-session",
            "timestamp": time.time(),
            "payload": {
                "type": "message",
                "content": "Hello WS",
                "metadata": {},
            },
        }
        ws.send_json(envelope)
        data = ws.receive_json()
        assert data["status"] == "success"
        assert "echo" in data["data"]
        assert data["data"]["echo"] == "Hello WS"


def test_ws_tool_call(client):
    """WebSocket /ws with ToolCallRequest envelope."""
    with client.websocket_connect("/ws") as ws:
        envelope = {
            "session_id": "ws-tool-session",
            "timestamp": time.time(),
            "payload": {
                "type": "tool_call",
                "tool_name": "calculator",
                "arguments": {"op": "mul", "a": 3, "b": 4},
            },
        }
        ws.send_json(envelope)
        data = ws.receive_json()
        assert data["status"] == "success"
        assert data["data"]["tool_name"] == "calculator"


def test_ws_multiple_messages(client):
    """WebSocket /ws handles multiple messages in sequence."""
    with client.websocket_connect("/ws") as ws:
        for i in range(3):
            envelope = {
                "session_id": f"ws-multi-{i}",
                "timestamp": time.time(),
                "payload": {
                    "type": "message",
                    "content": f"Message {i}",
                    "metadata": {},
                },
            }
            ws.send_json(envelope)
            data = ws.receive_json()
            assert data["status"] == "success"
            assert data["data"]["echo"] == f"Message {i}"


def test_ws_invalid_envelope_returns_error(client):
    """WebSocket /ws with invalid envelope → error response."""
    with client.websocket_connect("/ws") as ws:
        envelope = {
            "session_id": "ws-bad",
            "timestamp": 0,  # too old
            "payload": {"type": "message", "content": "test"},
        }
        ws.send_json(envelope)
        data = ws.receive_json()
        assert data["status"] == "error"
        assert "error" in data
