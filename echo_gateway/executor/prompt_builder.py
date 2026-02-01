"""
Prompt Builder — Phase 5

Converts session state to LLM messages format.
"""

from __future__ import annotations

from typing import Any, Dict, List


class PromptBuilder:
    """
    Builds LLM messages from session state.

    Phase 5: minimal implementation with system prompt + user message.
    Future phases: full conversation history + tool results.
    """

    def __init__(self, system_prompt: str = "You are a helpful assistant."):
        self.system_prompt = system_prompt

    def build_messages(
        self, *, session_state: Dict[str, Any], user_content: str
    ) -> List[Dict[str, Any]]:
        """
        Build messages list for LLM.

        Phase 5: system + user only.
        Future: include conversation history from session_state.
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # Future: add conversation history from session_state["history"]

        messages.append({"role": "user", "content": user_content})

        return messages

    def append_tool_result(
        self, messages: List[Dict[str, Any]], tool_call_id: str, result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Append tool result to messages.

        Phase 5: basic tool result format.
        """
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": str(result.get("result", "")),
            }
        )
        return messages
