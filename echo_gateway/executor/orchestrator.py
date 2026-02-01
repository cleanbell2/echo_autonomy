"""
Orchestrator — Phase 5

Tool-call loop + streaming orchestration.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from echo_gateway.session.store import SessionStore

from .llm_client import LLMClient
from .prompt_builder import PromptBuilder
from .streaming import StreamEvent
from .tool_registry import ToolRegistry
from .tool_runtime import ToolRuntime


class Orchestrator:
    """
    Orchestrates LLM + tool execution with streaming support.

    Flow:
    1. Build messages from session
    2. Call LLM (complete or stream)
    3. If tool_calls: execute tools, loop back
    4. Return final response
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        tool_runtime: ToolRuntime,
        prompt_builder: PromptBuilder,
        session_store: SessionStore,
        max_tool_iterations: int = 5,
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._tool_runtime = tool_runtime
        self._prompt_builder = prompt_builder
        self._session_store = session_store
        self._max_tool_iterations = max_tool_iterations

    async def run_message(
        self, *, session_id: str, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Non-streaming message execution.

        Returns:
            {"status": "success"|"error", "data": {...}, "error": str|None}
        """
        try:
            # Get session
            session = self._session_store.get_or_create(session_id)

            # Build messages
            messages = self._prompt_builder.build_messages(
                session_state=session.data, user_content=content
            )

            # Tool-call loop
            tools = self._tool_registry.to_llm_tools()
            iteration = 0

            while iteration < self._max_tool_iterations:
                iteration += 1

                # Call LLM
                response = await self._llm.complete(
                    messages=messages, tools=tools if tools else None
                )

                # Check for tool calls
                tool_calls = response.get("tool_calls")
                if not tool_calls:
                    # Final response
                    return {
                        "status": "success",
                        "data": {
                            "content": response.get("content"),
                            "finish_reason": response.get("finish_reason"),
                            "iterations": iteration,
                        },
                        "error": None,
                    }

                # Execute tool calls
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    args_str = func.get("arguments", "{}")

                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {}

                    # Get tool
                    try:
                        tool = self._tool_registry.get(tool_name)
                    except ValueError as e:
                        # Unknown tool → fail-closed
                        return {
                            "status": "error",
                            "data": {},
                            "error": f"Unknown tool: {tool_name}",
                        }

                    # Execute tool
                    result = await self._tool_runtime.execute(
                        tool=tool, arguments=args, session_id=session_id
                    )

                    # Check for tool error
                    if result.get("error"):
                        return {
                            "status": "error",
                            "data": {},
                            "error": f"Tool error: {result['error']}",
                        }

                    # Append tool result to messages
                    messages = self._prompt_builder.append_tool_result(
                        messages, tc.get("id", ""), result
                    )

            # Max iterations reached
            return {
                "status": "error",
                "data": {},
                "error": f"Max tool iterations reached: {self._max_tool_iterations}",
            }

        except Exception as e:
            # Fail-closed
            return {"status": "error", "data": {}, "error": f"Orchestrator error: {str(e)}"}

    async def stream_message(
        self, *, session_id: str, content: str, metadata: Dict[str, Any]
    ) -> AsyncIterator[StreamEvent]:
        """
        Streaming message execution.

        Yields StreamEvent until final.
        """
        try:
            # Get session
            session = self._session_store.get_or_create(session_id)

            # Build messages
            messages = self._prompt_builder.build_messages(
                session_state=session.data, user_content=content
            )

            # Tool-call loop
            tools = self._tool_registry.to_llm_tools()
            iteration = 0

            while iteration < self._max_tool_iterations:
                iteration += 1

                # Stream LLM
                accumulated_content = ""
                tool_calls_chunk = None

                async for chunk in self._llm.stream(
                    messages=messages, tools=tools if tools else None
                ):
                    delta = chunk.get("delta")
                    if delta:
                        accumulated_content += delta
                        yield StreamEvent(type="delta", data={"delta": delta})

                    tc = chunk.get("tool_calls")
                    if tc:
                        tool_calls_chunk = tc
                        yield StreamEvent(
                            type="tool_call", data={"tool_calls": tool_calls_chunk}
                        )

                    finish_reason = chunk.get("finish_reason")
                    if finish_reason:
                        if finish_reason == "stop":
                            # Final response
                            yield StreamEvent(
                                type="final",
                                data={
                                    "content": accumulated_content,
                                    "finish_reason": finish_reason,
                                    "iterations": iteration,
                                },
                            )
                            return
                        elif finish_reason == "tool_calls":
                            # Continue to tool execution
                            break

                # Check for tool calls
                if not tool_calls_chunk:
                    # No tool calls, end
                    yield StreamEvent(
                        type="final",
                        data={
                            "content": accumulated_content,
                            "finish_reason": "stop",
                            "iterations": iteration,
                        },
                    )
                    return

                # Execute tool calls
                for tc in tool_calls_chunk:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    args_str = func.get("arguments", "{}")

                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {}

                    # Get tool
                    try:
                        tool = self._tool_registry.get(tool_name)
                    except ValueError as e:
                        yield StreamEvent(
                            type="error", data={}, error=f"Unknown tool: {tool_name}"
                        )
                        return

                    # Execute tool
                    result = await self._tool_runtime.execute(
                        tool=tool, arguments=args, session_id=session_id
                    )

                    # Yield tool result
                    yield StreamEvent(
                        type="tool_result",
                        data={"tool_name": tool_name, "result": result},
                    )

                    # Check for tool error
                    if result.get("error"):
                        yield StreamEvent(
                            type="error", data={}, error=f"Tool error: {result['error']}"
                        )
                        return

                    # Append tool result to messages
                    messages = self._prompt_builder.append_tool_result(
                        messages, tc.get("id", ""), result
                    )

            # Max iterations reached
            yield StreamEvent(
                type="error",
                data={},
                error=f"Max tool iterations reached: {self._max_tool_iterations}",
            )

        except Exception as e:
            # Fail-closed
            yield StreamEvent(type="error", data={}, error=f"Orchestrator error: {str(e)}")
