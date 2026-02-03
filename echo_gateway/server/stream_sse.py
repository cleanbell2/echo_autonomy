"""
HTTP Server-Sent Events (SSE) streaming endpoint for Phase 6.

Provides POST /api/stream that:
- Accepts an envelope dict
- Streams orchestrator events via SSE format
- Emits: event: delta/final/error with data: {...}
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, AsyncIterator

from sse_starlette.sse import EventSourceResponse

from echo_gateway.executor.streaming import StreamEvent, StreamEventType
from echo_gateway.gateway.wiring import create_orchestrator

if TYPE_CHECKING:
    from fastapi import Request


async def stream_events(
    envelope: dict,
    request: Request,
) -> AsyncIterator[dict]:
    """
    Stream orchestrator events as SSE-compatible dicts.
    
    Args:
        envelope: Client envelope with session_id, timestamp, payload
        request: FastAPI request (to access app.state)
    
    Yields:
        dict with 'event' and 'data' keys for SSE
    """
    # Extract session_id and payload
    session_id = envelope.get("session_id", "unknown")
    payload = envelope.get("payload", {})
    content = payload.get("content", "")
    metadata = payload.get("metadata", {})
    
    # Build orchestrator
    orchestrator = create_orchestrator(request)
    
    # Stream orchestrator events
    async for event in orchestrator.stream_message(
        session_id=session_id,
        content=content,
        metadata=metadata,
    ):
        # Map StreamEvent to SSE format
        sse_event = _stream_event_to_sse(event)
        yield sse_event
        
        # Stop on final or error
        if event.type in {StreamEventType.FINAL, StreamEventType.ERROR}:
            break


def _stream_event_to_sse(event: StreamEvent) -> dict:
    """
    Convert StreamEvent to SSE-compatible dict.
    
    Args:
        event: StreamEvent from orchestrator
    
    Returns:
        dict with 'event' and 'data' keys
    """
    # Map event type to SSE event name
    event_name = event.type.value  # "delta", "tool_call", "tool_result", "final", "error"
    
    # Build data payload
    data = {
        "type": event.type.value,
        "data": event.data,
    }
    
    if event.error:
        data["error"] = event.error
    
    return {
        "event": event_name,
        "data": json.dumps(data),
    }


async def stream_sse_endpoint(
    envelope: dict,
    request: Request,
) -> EventSourceResponse:
    """
    SSE endpoint handler for POST /api/stream.
    
    Args:
        envelope: Client envelope dict
        request: FastAPI request
    
    Returns:
        EventSourceResponse with streaming events
    """
    return EventSourceResponse(
        stream_events(envelope, request),
        media_type="text/event-stream",
    )
