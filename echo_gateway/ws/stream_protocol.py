"""
WebSocket streaming protocol for Phase 6.

Defines RPC stream event types:
- Client -> Server: rpc.stream (request streaming response)
- Server -> Client: rpc.stream.delta, rpc.stream.final, rpc.stream.error
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from echo_gateway.executor.streaming import StreamEvent, StreamEventType

if TYPE_CHECKING:
    from echo_gateway.executor import Orchestrator


async def handle_stream_request(
    envelope: dict,
    orchestrator: Orchestrator,
) -> AsyncIterator[dict]:
    """
    Handle WebSocket streaming request.
    
    Args:
        envelope: Client envelope with session_id, timestamp, payload
        orchestrator: Orchestrator instance
    
    Yields:
        Response envelopes with rpc.stream.* events
    """
    # Extract fields
    session_id = envelope.get("session_id", "unknown")
    payload = envelope.get("payload", {})
    request_type = payload.get("type", "")
    
    # Only handle rpc.stream
    if request_type != "rpc.stream":
        yield {
            "session_id": session_id,
            "payload": {
                "type": "rpc.stream.error",
                "error": f"Unknown request type: {request_type}",
            },
        }
        return
    
    content = payload.get("content", "")
    metadata = payload.get("metadata", {})
    
    # Stream orchestrator events
    try:
        async for event in orchestrator.stream_message(
            session_id=session_id,
            content=content,
            metadata=metadata,
        ):
            # Map StreamEvent to WebSocket response
            ws_response = _stream_event_to_ws(event, session_id)
            yield ws_response
            
            # Stop on final or error
            if event.type in {StreamEventType.FINAL, StreamEventType.ERROR}:
                break
    except Exception as e:
        # Fail-closed: emit error
        yield {
            "session_id": session_id,
            "payload": {
                "type": "rpc.stream.error",
                "error": str(e),
            },
        }


def _stream_event_to_ws(event: StreamEvent, session_id: str) -> dict:
    """
    Convert StreamEvent to WebSocket response envelope.
    
    Args:
        event: StreamEvent from orchestrator
        session_id: Session identifier
    
    Returns:
        Response envelope dict
    """
    # Map event type to WebSocket response type
    type_map = {
        StreamEventType.DELTA: "rpc.stream.delta",
        StreamEventType.TOOL_CALL: "rpc.stream.tool_call",
        StreamEventType.TOOL_RESULT: "rpc.stream.tool_result",
        StreamEventType.FINAL: "rpc.stream.final",
        StreamEventType.ERROR: "rpc.stream.error",
        StreamEventType.DEBUG: "rpc.stream.debug",
    }
    
    response_type = type_map.get(event.type, "rpc.stream.error")
    
    payload = {
        "type": response_type,
        "data": event.data,
    }
    
    if event.error:
        payload["error"] = event.error
    
    return {
        "session_id": session_id,
        "payload": payload,
    }
