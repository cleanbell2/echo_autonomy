"""
Test orchestrator — message (non-streaming) — Phase 5
"""

import pytest

from echo_gateway.executor.fake_llm_client import FakeLLMClient
from echo_gateway.executor.orchestrator import Orchestrator
from echo_gateway.executor.prompt_builder import PromptBuilder
from echo_gateway.executor.tool_registry import ToolRegistry
from echo_gateway.executor.tool_runtime import ToolRuntime
from echo_gateway.session.store import SessionStore


@pytest.mark.asyncio
async def test_orchestrator_message_no_tools():
    """Orchestrator handles message without tool calls."""
    llm = FakeLLMClient(mode="echo")
    registry = ToolRegistry()
    runtime = ToolRuntime()
    builder = PromptBuilder()
    store = SessionStore()

    orch = Orchestrator(
        llm=llm,
        tool_registry=registry,
        tool_runtime=runtime,
        prompt_builder=builder,
        session_store=store,
    )

    result = await orch.run_message(
        session_id="test-session", content="Hello", metadata={}
    )

    assert result["status"] == "success"
    assert "Echo: Hello" in result["data"]["content"]
    assert result["error"] is None


@pytest.mark.asyncio
async def test_orchestrator_message_unknown_tool():
    """Orchestrator blocks unknown tool calls."""
    # Use custom FakeLLMClient that returns unknown tool
    class UnknownToolLLM:
        async def complete(self, *, messages, tools=None, temperature=0.2):
            return {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "unknown_tool",  # Not registered
                            "arguments": "{}",
                        },
                    }
                ],
                "finish_reason": "tool_calls",
            }

        async def stream(self, *, messages, tools=None, temperature=0.2):
            yield {
                "delta": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "unknown_tool", "arguments": "{}"},
                    }
                ],
                "finish_reason": None,
            }

    llm = UnknownToolLLM()
    registry = ToolRegistry()
    runtime = ToolRuntime()
    builder = PromptBuilder()
    store = SessionStore()

    # Register no tools

    orch = Orchestrator(
        llm=llm,
        tool_registry=registry,
        tool_runtime=runtime,
        prompt_builder=builder,
        session_store=store,
    )

    result = await orch.run_message(
        session_id="test-session", content="Call tool", metadata={}
    )

    assert result["status"] == "error"
    assert "Unknown tool" in result["error"]


@pytest.mark.asyncio
async def test_orchestrator_message_max_iterations():
    """Orchestrator stops at max iterations."""
    llm = FakeLLMClient(mode="tool")
    registry = ToolRegistry()
    runtime = ToolRuntime()
    builder = PromptBuilder()
    store = SessionStore()

    # Create infinite loop tool
    class LoopTool:
        from echo_gateway.executor.tool_registry import ToolSpec

        spec = ToolSpec(
            name="loop_tool",
            description="Loops forever",
            input_schema={"type": "object", "properties": {}, "required": []},
        )

        async def run(self, *, arguments, session_id):
            return {"result": "loop", "error": None}

    registry.register(LoopTool())

    orch = Orchestrator(
        llm=llm,
        tool_registry=registry,
        tool_runtime=runtime,
        prompt_builder=builder,
        session_store=store,
        max_tool_iterations=2,
    )

    result = await orch.run_message(
        session_id="test-session", content="Loop forever", metadata={}
    )

    assert result["status"] == "error"
    assert "Max tool iterations" in result["error"]
