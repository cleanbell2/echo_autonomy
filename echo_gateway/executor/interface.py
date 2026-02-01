"""
Executor interface — Phase 4

Defines the protocol for handling message/tool/status requests.
All implementations must be async and return ExecResult.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Protocol

Status = Literal["success", "error", "pending"]


@dataclass(frozen=True)
class ExecResult:
    """
    Result of an executor operation.

    - status: "success" | "error" | "pending"
    - data: arbitrary JSON-serializable dict
    - error: optional error message (non-None when status="error")
    """

    status: Status
    data: Dict[str, Any]
    error: Optional[str] = None


class Executor(Protocol):
    """
    Protocol for executing gateway requests.

    All methods are async and return ExecResult.
    Implementations must be fail-closed: unexpected errors → status="error".
    """

    async def handle_message(
        self, session_id: str, content: str, metadata: Dict[str, Any]
    ) -> ExecResult:
        """Handle a MessageRequest."""
        ...

    async def handle_tool_call(
        self, session_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> ExecResult:
        """Handle a ToolCallRequest."""
        ...

    async def handle_status(self, session_id: str, status: str) -> ExecResult:
        """Handle a StatusRequest."""
        ...
