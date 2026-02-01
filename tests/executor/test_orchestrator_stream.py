"""
Test orchestrator — streaming — Phase 5
"""

import pytest

from echo_gateway.executor.fake_llm_client import FakeLLMClient
from echo_gateway.executor.orchestrator import Orchestrator
from echo_gateway.executor.prompt_builder import PromptBuilder
from echo_gateway.executor.tool_registry import ToolRegistry, ToolSpec
from echo_gateway.executor.tool_runtime import ToolRuntime
from echo_gateway.session.store import SessionStore


@pytest.mark.asyncio
async def test_orchestrator_stream_no_tools():
    """Orchestrator streams message without tool calls."""
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

    events = []
    async for event in orch.stream_message(
        session_id="test-session", content="Hello", metadata={}
    ):
        events.append(event)

    # Should have delta events + final
    assert any(e.type == "delta" for e in events)
    assert any(e.type == "final" for e in events)

    final = next(e for e in events if e.type == "final")
    assert "Hello" in final.data.get("content", "")


@pytest.mark.asyncio
async def test_orchestrator_stream_with_tool_call():
    """Orchestrator streams with tool call and result."""
    llm = FakeLLMClient(mode="tool")
    registry = ToolRegistry()
    runtime = ToolRuntime()
    builder = PromptBuilder()
    store = SessionStore()

    # Register test tool
    class TestTool:
        spec = ToolSpec(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"test": {"type": "string"}},
                "required": [],
            },
        )

        async def run(self, *, arguments, session_id):
            return {"result": "tool_result", "error": None}

    registry.register(TestTool())

    orch = Orchestrator(
        llm=llm,
        tool_registry=registry,
        tool_runtime=runtime,
        prompt_builder=builder,
        session_store=store,
    )

    events = []
    async for event in orch.stream_message(
        session_id="test-session", content="Call tool", metadata={}
    ):
        events.append(event)

    # Should have tool_call + tool_result events
    assert any(e.type == "tool_call" for e in events)
    assert any(e.type == "tool_result" for e in events)


@pytest.mark.asyncio
async def test_orchestrator_stream_unknown_tool():
    """Orchestrator streams error for unknown tool."""
    # Use custom LLM that returns unknown tool
    class UnknownToolLLM:
        async def complete(self, *, messages, tools=None, temperature=0.2):
            return {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "unknown_tool", "arguments": "{}"},
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
            yield {"delta": None, "tool_calls": None, "finish_reason": "tool_calls"}

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

    events = []
    async for event in orch.stream_message(
        session_id="test-session", content="Call tool", metadata={}
    ):
        events.append(event)

    # Should have error event
    error_events = [e for e in events if e.type == "error"]
    assert len(error_events) > 0
    assert "Unknown tool" in error_events[0].error
