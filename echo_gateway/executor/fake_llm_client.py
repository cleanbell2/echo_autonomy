"""
Fake LLM Client — Phase 5 Testing

Simulates LLM responses without external API calls.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional


class FakeLLMClient:
    """
    Fake LLM client for testing.

    Returns predefined responses based on message content.
    """

    def __init__(self, *, mode: str = "echo"):
        """
        mode:
        - "echo": echoes back user message
        - "tool": requests tool call
        - "stream": simulates streaming
        """
        self.mode = mode

    async def complete(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Non-streaming completion."""
        if self.mode == "tool" and tools and len(tools) > 0:
            return {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": tools[0]["function"]["name"],
                            "arguments": '{"test": "value"}',
                        },
                    }
                ],
                "finish_reason": "tool_calls",
            }
        else:
            user_msg = next(
                (m["content"] for m in messages if m.get("role") == "user"), "..."
            )
            return {
                "content": f"Echo: {user_msg}",
                "tool_calls": None,
                "finish_reason": "stop",
            }

    async def stream(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Streaming completion."""
        if self.mode == "tool" and tools and len(tools) > 0:
            yield {
                "delta": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": tools[0]["function"]["name"],
                            "arguments": '{"test": "value"}',
                        },
                    }
                ],
                "finish_reason": None,
            }
            yield {"delta": None, "tool_calls": None, "finish_reason": "tool_calls"}
        else:
            user_msg = next(
                (m["content"] for m in messages if m.get("role") == "user"), "..."
            )
            for chunk in ["Echo: ", user_msg]:
                yield {"delta": chunk, "tool_calls": None, "finish_reason": None}
            yield {"delta": None, "tool_calls": None, "finish_reason": "stop"}
