"""
Gateway pipeline — Phase 4

handle_inbound: envelope → sanitize → parse → safety → execute → response
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal

from echo_gateway.protocol.envelope import Envelope
from echo_gateway.protocol.schemas import (
    MessageRequest,
    StatusRequest,
    ToolCallRequest,
    parse_request,
)
from echo_gateway.protocol.validator import (
    ensure_json_serializable,
    sanitize_payload,
    sanitize_session_id,
)

SafetyLevel = Literal["ALLOW", "WARN", "BLOCK"]


@dataclass(frozen=True)
class SafetyDecision:
    """Result of a safety check."""

    level: SafetyLevel
    reason: str = ""


# Type alias for safety check callable
SafetyCheck = Callable[[str, Dict[str, Any]], SafetyDecision]


async def handle_inbound(
    envelope_dict: Dict[str, Any], executor, safety_check: SafetyCheck
) -> Dict[str, Any]:
    """
    Process inbound request through gateway pipeline.

    Steps:
    1. Parse envelope structure
    2. Sanitize session_id + validate recency
    3. Sanitize payload + ensure JSON-serializable
    4. Parse request type
    5. Safety check (inbound stage)
    6. Execute via executor
    7. Safety check for tool calls (stricter)
    8. Return response dict

    Returns:
        {"status": "success"|"error"|"pending", "data": {...}, "error": str|None}
    """
    try:
        # 1) Parse envelope
        env = Envelope.from_dict(envelope_dict)

        # 2) Sanitize + validate
        clean_sid = sanitize_session_id(env.session_id)
        env = Envelope(
            session_id=clean_sid,
            payload=env.payload,
            timestamp=env.timestamp,
            signature=env.signature,
        )
        env.validate()

        # 3) Sanitize payload
        payload = sanitize_payload(env.payload)
        ensure_json_serializable(payload)

        # 4) Parse request
        req = parse_request(payload)

        # 5) Safety check — inbound
        decision = safety_check("inbound", payload)
        if decision.level == "BLOCK":
            return {
                "status": "error",
                "data": {},
                "error": f"Blocked by safety policy: {decision.reason}",
            }

        # 6) Execute
        if isinstance(req, MessageRequest):
            r = await executor.handle_message(
                env.session_id, req.content, req.metadata
            )
        elif isinstance(req, ToolCallRequest):
            # 7) Tool stage safety check (stricter)
            tool_decision = safety_check("tool", payload)
            if tool_decision.level == "BLOCK":
                return {
                    "status": "error",
                    "data": {},
                    "error": f"Blocked tool execution: {tool_decision.reason}",
                }
            r = await executor.handle_tool_call(
                env.session_id, req.tool_name, req.arguments
            )
        elif isinstance(req, StatusRequest):
            r = await executor.handle_status(env.session_id, req.status)
        else:
            return {"status": "error", "data": {}, "error": "Unknown request type"}

        # 8) Response
        return {"status": r.status, "data": r.data, "error": r.error}

    except Exception as e:
        # Fail-closed: unexpected errors → error response
        return {"status": "error", "data": {}, "error": f"Gateway error: {str(e)}"}
