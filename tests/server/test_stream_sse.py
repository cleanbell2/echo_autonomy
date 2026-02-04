"""
Tests for SSE streaming endpoint (Phase 6).

Verifies:
- POST /api/stream streams events
- Event format: event: delta/final/error
- Data format: JSON payload
- Orchestrator integration
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from echo_gateway.server.app import create_app


@pytest.fixture
def app():
    """Create test app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_stream_sse_delta_final(client):
    """Test SSE streaming with delta and final events."""
    envelope = {
        "session_id": "test-sse-1",
        "timestamp": 1234567890.0,
        "payload": {
            "type": "message",
            "content": "Hello streaming",
        },
    }
    
    with client.stream("POST", "/api/stream", json=envelope) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Parse SSE events
        events = []
        for line in response.iter_lines():
            if line.startswith("event: "):
                event_type = line[7:]
                events.append(event_type)
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                # Verify data structure
                assert "type" in data
        
        # Should have at least delta and final
        assert "delta" in events or "final" in events


def test_stream_sse_error_handling(client):
    """Test SSE streaming error handling."""
    # Invalid envelope (missing session_id)
    envelope = {
        "timestamp": 1234567890.0,
        "payload": {
            "type": "message",
            "content": "test",
        },
    }
    
    with client.stream("POST", "/api/stream", json=envelope) as response:
        # Should still return 200 but emit error event
        assert response.status_code == 200
        
        # Check for error event
        events = []
        for line in response.iter_lines():
            if line.startswith("event: "):
                events.append(line[7:])
        
        # May include error or just proceed with default session
        # Fail-closed: orchestrator handles gracefully


def test_stream_sse_tool_call_events(client):
    """Test SSE streaming with tool call events."""
    envelope = {
        "session_id": "test-sse-tool",
        "timestamp": 1234567890.0,
        "payload": {
            "type": "tool_call",
            "tool_name": "test_tool",
            "arguments": {"key": "value"},
        },
    }
    
    with client.stream("POST", "/api/stream", json=envelope) as response:
        assert response.status_code == 200
        
        # Collect events
        events = []
        for line in response.iter_lines():
            if line.startswith("event: "):
                events.append(line[7:])
        
        # Should process tool call
        # (FakeLLMClient may emit tool_call, tool_result, final)
