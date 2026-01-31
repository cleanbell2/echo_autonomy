"""
WebSocket router — Phase 4

/ws: accept envelope dicts, run through gateway pipeline, send response
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from echo_gateway.gateway.pipeline import handle_inbound

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """
    WebSocket RPC endpoint.

    Expects JSON envelope, runs through gateway pipeline, returns response.
    """
    await ws.accept()

    # Access app state for executor/safety
    executor = ws.app.state.executor
    safety_check = ws.app.state.safety_check

    try:
        while True:
            msg = await ws.receive_json()
            response = await handle_inbound(msg, executor, safety_check)
            await ws.send_json(response)
    except WebSocketDisconnect:
        return
