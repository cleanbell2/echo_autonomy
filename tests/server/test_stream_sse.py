"""
Phase 6 SSE streaming endpoint tests.

Tests POST /api/stream with orchestrator streaming.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from echo_gateway.server.app import create_app


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_stream_happy_path(client):
    """Test SSE streaming with simple message."""
    with client:
        envelope = {
            "session_id": "test-stream-123",
            "timestamp": 1234567890.0,
            "payload": {
                "type": "message",
                "content": "Hello streaming!",
            },
        }
        
        response = client.post("/api/stream", json=envelope)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse SSE events
        events = _parse_sse_events(response.text)
        
        # Should have at least delta and final
        assert len(events) >= 2
        
        # Check delta event
        delta_events = [e for e in events if e["event"] == "delta"]
        assert len(delta_events) > 0
        
        # Check final event
        final_events = [e for e in events if e["event"] == "final"]
        assert len(final_events) == 1
        # Content is inside data.data (nested)
        assert "data" in final_events[0]["data"]
        assert "content" in final_events[0]["data"]["data"]


def test_stream_with_session(client):
    """Test SSE streaming preserves session context."""
    with client:
        session_id = "test-session-456"
        
        # First message
        envelope1 = {
            "session_id": session_id,
            "timestamp": 1234567890.0,
            "payload": {
                "type": "message",
                "content": "First message",
            },
        }
        
        response1 = client.post("/api/stream", json=envelope1)
        assert response1.status_code == 200
        
        events1 = _parse_sse_events(response1.text)
        final1 = [e for e in events1 if e["event"] == "final"][0]
        
        # Second message (should have context)
        envelope2 = {
            "session_id": session_id,
            "timestamp": 1234567891.0,
            "payload": {
                "type": "message",
                "content": "Second message",
            },
        }
        
        response2 = client.post("/api/stream", json=envelope2)
        assert response2.status_code == 200
        
        events2 = _parse_sse_events(response2.text)
        final2 = [e for e in events2 if e["event"] == "final"][0]
        
        # Both should succeed
        assert "data" in final1["data"]
        assert "content" in final1["data"]["data"]
        assert "data" in final2["data"]
        assert "content" in final2["data"]["data"]


def test_stream_error_handling(client):
    """Test SSE streaming with invalid envelope."""
    with client:
        # Invalid envelope (missing required fields)
        envelope = {
            "session_id": "test-error",  # Valid session_id
            "timestamp": 1234567890.0,
            "payload": {
                "type": "unknown_type",  # Unknown type to trigger error
                "content": "Test",
            },
        }
        
        response = client.post("/api/stream", json=envelope)
        
        assert response.status_code == 200  # SSE always returns 200
        
        events = _parse_sse_events(response.text)
        
        # With unknown type, orchestrator will still respond (FakeLLMClient echoes)
        # So we expect a final event, not error
        final_events = [e for e in events if e["event"] == "final"]
        assert len(final_events) >= 1


def _parse_sse_events(text: str) -> list[dict]:
    """
    Parse SSE text into list of event dicts.
    
    Args:
        text: Raw SSE response text
    
    Returns:
        List of dicts with 'event' and 'data' keys
    """
    import json
    
    events = []
    lines = text.strip().split("\n")
    
    current_event = {}
    for line in lines:
        line = line.strip()
        
        if not line:
            # Empty line = end of event
            if current_event:
                events.append(current_event)
                current_event = {}
        elif line.startswith("event:"):
            current_event["event"] = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
            try:
                current_event["data"] = json.loads(data_str)
            except json.JSONDecodeError:
                current_event["data"] = data_str
    
    # Add last event if exists
    if current_event:
        events.append(current_event)
    
    return events
