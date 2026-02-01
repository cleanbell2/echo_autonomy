"""
LLM Client Protocol — Phase 5

Provider-agnostic interface for LLM completion and streaming.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class LLMClient(Protocol):
    """
    Protocol for LLM completion.

    Implementations must be provider-agnostic:
    - complete: non-streaming completion
    - stream: streaming completion yielding chunks
    """

    async def complete(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Non-streaming completion.

        Returns provider-agnostic response dict:
        {
            "content": str | None,
            "tool_calls": List[Dict] | None,
            "finish_reason": str
        }
        """
        ...

    async def stream(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming completion.

        Yields provider-agnostic chunks:
        {
            "delta": str | None,
            "tool_calls": List[Dict] | None,
            "finish_reason": str | None
        }
        """
        ...
