"""
HTTP routes — Phase 6

/health: readiness check
/api/message: synchronous message endpoint (uses gateway pipeline)
/api/stream: SSE streaming endpoint (Phase 6)
"""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from echo_gateway.executor import Orchestrator
from echo_gateway.gateway.pipeline import SafetyCheck, handle_inbound

from .deps import get_executor, get_orchestrator, get_safety_check

router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"ok": True, "service": "echo_gateway", "phase": 6}


@router.post("/api/message")
async def api_message(
    envelope: Dict[str, Any],
    executor=Depends(get_executor),
    safety_check: SafetyCheck = Depends(get_safety_check),
) -> Dict[str, Any]:
    """
    Synchronous message endpoint.

    Expects envelope dict, runs through gateway pipeline.
    """
    return await handle_inbound(envelope, executor, safety_check)


@router.post("/api/stream")
async def api_stream(
    envelope: Dict[str, Any],
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """
    SSE streaming endpoint (Phase 6).

    Accepts envelope dict, streams StreamEvent as Server-Sent Events.

    Event format:
        event: delta
        data: {"delta": "text chunk"}

        event: final
        data: {"content": "...", "finish_reason": "stop"}

        event: error
        data: {"error": "error message"}
    """

    async def event_generator():
        try:
            # Extract envelope fields
            session_id = envelope.get("session_id", "default")
            payload = envelope.get("payload", {})
            content = payload.get("content", "")
            metadata = payload.get("metadata", {})

            # Stream from orchestrator
            async for event in orchestrator.stream_message(
                session_id=session_id, content=content, metadata=metadata
            ):
                # Convert StreamEvent to SSE format
                # event.type is StreamEventType enum, get value
                event_type = event.type.value if hasattr(event.type, "value") else str(event.type)
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event.to_dict())}\n\n"

        except Exception as e:
            # Fail-closed: stream error event
            yield f"event: error\n"
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")
