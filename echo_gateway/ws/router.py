"""
WebSocket router — Phase 6

/ws: accept envelope dicts, support both sync RPC and streaming
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from echo_gateway.gateway.pipeline import handle_inbound
from echo_gateway.gateway.wiring import create_orchestrator
from echo_gateway.ws.stream_protocol import handle_stream_request

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """
    WebSocket RPC endpoint with streaming support (Phase 6).

    Supports two modes:
    1. Sync RPC (Phase 4): {"session_id": ..., "payload": {"type": "message", ...}}
    2. Stream RPC (Phase 6): {"session_id": ..., "payload": {"type": "rpc.stream", ...}}

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
            envelope = await ws.receive_json()

            # Check payload type for streaming
            payload = envelope.get("payload", {})
            request_type = payload.get("type", "")

            if request_type == "rpc.stream":
                # Streaming mode (Phase 6) - use stream protocol
                async for response in handle_stream_request(envelope, orchestrator):
                    await ws.send_json(response)
            else:
                # Sync RPC mode (Phase 4 compatibility)
                response = await handle_inbound(envelope, executor, safety_check)
                await ws.send_json(response)

    except WebSocketDisconnect:
        return
