"""
HTTP routes — Phase 4

/health: readiness check
/api/message: synchronous message endpoint (uses gateway pipeline)
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from echo_gateway.gateway.pipeline import SafetyCheck, handle_inbound

from .deps import get_executor, get_safety_check

router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"ok": True, "service": "echo_gateway", "phase": 4}


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
