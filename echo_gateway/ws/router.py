"""
WebSocket router — Phase 6

/ws: accept envelope dicts, support both sync RPC and streaming
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from echo_gateway.gateway.pipeline import handle_inbound
from echo_gateway.gateway.wiring import create_orchestrator

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """
    WebSocket RPC endpoint with streaming support (Phase 6).

    Supports two modes:
    1. Sync RPC (Phase 4): {"session_id": ..., "payload": ...}
    2. Stream RPC (Phase 6): {"type": "rpc.stream", "payload": {...}}

    Stream events:
        rpc.stream.delta — text chunk
        rpc.stream.tool_call — tool call request
        rpc.stream.tool_result — tool execution result
        rpc.stream.final — final response
        rpc.stream.error — error event
    """
    await ws.accept()

    # Access app state
    executor = ws.app.state.executor
    safety_check = ws.app.state.safety_check

    # Create orchestrator (lazy init)
    if not hasattr(ws.app.state, "orchestrator"):
        session_store = ws.app.state.session_store
        ws.app.state.orchestrator = create_orchestrator(session_store)
    orchestrator = ws.app.state.orchestrator

    try:
        while True:
            msg = await ws.receive_json()

            # Check if streaming request
            if msg.get("type") == "rpc.stream":
                # Streaming mode (Phase 6)
                envelope = msg.get("payload", {})
                session_id = envelope.get("session_id", "default")
                payload = envelope.get("payload", {})
                content = payload.get("content", "")
                metadata = payload.get("metadata", {})

                try:
                    # Stream events
                    async for event in orchestrator.stream_message(
                        session_id=session_id, content=content, metadata=metadata
                    ):
                        await ws.send_json(
                            {
                                "type": f"rpc.stream.{event.type}",
                                "data": event.data,
                                "error": event.error,
                            }
                        )
                except Exception as e:
                    # Fail-closed: send error event
                    await ws.send_json(
                        {
                            "type": "rpc.stream.error",
                            "data": {},
                            "error": str(e),
                        }
                    )
            else:
                # Sync RPC mode (Phase 4 compatibility)
                response = await handle_inbound(msg, executor, safety_check)
                await ws.send_json(response)

    except WebSocketDisconnect:
        return
