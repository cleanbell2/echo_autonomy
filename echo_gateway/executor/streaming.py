"""
Streaming event standard — Phase 5

Unified event format for HTTP SSE and WebSocket streaming.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

StreamEventType = Literal[
    "delta",  # Model text chunk
    "tool_call",  # Tool call request
    "tool_result",  # Tool execution result
    "final",  # Final response
    "error",  # Error event
    "debug",  # Debug/observability (optional)
]


@dataclass(frozen=True)
class StreamEvent:
    """
    Unified streaming event.

    - type: event type
    - data: event-specific payload
    - error: optional error message (non-None when type="error")
    """

    type: StreamEventType
    data: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": self.type,
            "data": self.data,
            "error": self.error,
        }
