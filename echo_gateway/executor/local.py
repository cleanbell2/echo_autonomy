"""
LocalExecutor — Phase 4 stub implementation

Echoes requests back with minimal processing.
Future phases will integrate real LLM/tool execution.
"""

from __future__ import annotations

from typing import Any, Dict

from .interface import ExecResult


class LocalExecutor:
    """
    Stub executor for Phase 4.

    Echoes requests back with status="success" and minimal processing.
    """

    async def handle_message(
        self, session_id: str, content: str, metadata: Dict[str, Any]
    ) -> ExecResult:
        """Echo message back."""
        return ExecResult(
            status="success",
            data={"echo": content, "session_id": session_id, "metadata": metadata},
            error=None,
        )

    async def handle_tool_call(
        self, session_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> ExecResult:
        """Echo tool call back."""
        return ExecResult(
            status="success",
            data={
                "tool_name": tool_name,
                "arguments": arguments,
                "session_id": session_id,
                "note": "Phase 4 stub — no real tool execution",
            },
            error=None,
        )

    async def handle_status(self, session_id: str, status: str) -> ExecResult:
        """Echo status back."""
        return ExecResult(
            status="success",
            data={"received_status": status, "session_id": session_id},
            error=None,
        )
