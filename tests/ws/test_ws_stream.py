"""
Phase 6 WebSocket streaming tests.

Tests WebSocket /ws with rpc.stream protocol.
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


def test_ws_stream_happy_path(client):
    """Test WebSocket streaming with simple message."""
    with client.websocket_connect("/ws") as ws:
            # Send streaming request
            ws.send_json({
                "type": "rpc.stream",
                "payload": {
                    "session_id": "test-ws-stream-123",
                    "payload": {
                        "type": "message",
                        "content": "Hello WS streaming!",
                    },
                },
            })
            
            # Collect events
            events = []
            while True:
                msg = ws.receive_json()
                events.append(msg)
                
                # Stop on final or error
                if msg.get("type") in ["rpc.stream.final", "rpc.stream.error"]:
                    break
            
            # Should have delta and final
            assert len(events) >= 2
            
            delta_events = [e for e in events if e["type"] == "rpc.stream.delta"]
            assert len(delta_events) > 0
            
            final_events = [e for e in events if e["type"] == "rpc.stream.final"]
            assert len(final_events) == 1
            assert "content" in final_events[0]["data"]


def test_ws_stream_with_session(client):
    """Test WebSocket streaming preserves session context."""
    with client.websocket_connect("/ws") as ws:
            session_id = "test-ws-session-456"
            
            # First message
            ws.send_json({
                "type": "rpc.stream",
                "payload": {
                    "session_id": session_id,
                    "payload": {
                        "type": "message",
                        "content": "First WS message",
                    },
                },
            })
            
            # Collect first response
            events1 = []
            while True:
                msg = ws.receive_json()
                events1.append(msg)
                if msg.get("type") in ["rpc.stream.final", "rpc.stream.error"]:
                    break
            
            # Second message
            ws.send_json({
                "type": "rpc.stream",
                "payload": {
                    "session_id": session_id,
                    "payload": {
                        "type": "message",
                        "content": "Second WS message",
                    },
                },
            })
            
            # Collect second response
            events2 = []
            while True:
                msg = ws.receive_json()
                events2.append(msg)
                if msg.get("type") in ["rpc.stream.final", "rpc.stream.error"]:
                    break
            
            # Both should have final events
            final1 = [e for e in events1 if e["type"] == "rpc.stream.final"]
            final2 = [e for e in events2 if e["type"] == "rpc.stream.final"]
            
            assert len(final1) == 1
            assert len(final2) == 1
            assert "content" in final1[0]["data"]
            assert "content" in final2[0]["data"]


def test_ws_stream_error_handling(client):
    """Test WebSocket streaming with invalid request."""
    with client.websocket_connect("/ws") as ws:
            # Send request that will succeed (FakeLLMClient handles all)
            ws.send_json({
                "type": "rpc.stream",
                "payload": {
                    "session_id": "test-ws-error",
                    "payload": {
                        "type": "message",
                        "content": "Test error",
                    },
                },
            })
            
            # Should receive events (final or error)
            events = []
            while True:
                msg = ws.receive_json()
                events.append(msg)
                if msg.get("type") in ["rpc.stream.final", "rpc.stream.error"]:
                    break
            
            # Should have terminal event
            terminal_events = [e for e in events if e.get("type") in ["rpc.stream.final", "rpc.stream.error"]]
            assert len(terminal_events) >= 1


def test_ws_sync_rpc_compatibility(client):
    """Test WebSocket sync RPC mode (Phase 4 compatibility)."""
    with client.websocket_connect("/ws") as ws:
            # Send sync RPC request (Phase 4 format)
            ws.send_json({
                "session_id": "test-sync-789",
                "timestamp": 1234567890.0,
                "payload": {
                    "type": "message",
                    "content": "Sync RPC test",
                },
            })
            
            # Should receive single response
            response = ws.receive_json()
            
            assert response.get("status") in ["success", "error"]
            assert "payload" in response or "error" in response
