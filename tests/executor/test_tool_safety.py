import pytest
from unittest.mock import AsyncMock, MagicMock
from echo_gateway.executor.orchestrator import Orchestrator
from echo_gateway.executor.tool_registry import ToolRegistry, ToolSpec
from echo_gateway.executor.tool_runtime import ToolRuntime
from echo_gateway.executor.prompt_builder import PromptBuilder
from echo_gateway.session.store import SessionStore


# 1. Broken Tool (Always fails)
class BrokenTool:
    spec = ToolSpec(
        name="broken_tool",
        description="A tool that always fails",
        input_schema={
            "type": "object",
            "properties": {
                "arg": {"type": "string"}
            },
            "required": ["arg"]
        }
    )
    
    async def run(self, *, arguments: dict, session_id: str):
        raise ValueError("System Failure")


# 2. Ping Tool (Always succeeds)
class PingTool:
    spec = ToolSpec(
        name="ping",
        description="A simple ping tool",
        input_schema={
            "type": "object",
            "properties": {
                "arg": {"type": "string"}
            },
            "required": ["arg"]
        }
    )
    
    async def run(self, *, arguments: dict, session_id: str):
        return {"result": "pong", "error": None}


@pytest.mark.asyncio
async def test_tool_safety_fail_closed():
    """Test if system handles tool errors gracefully"""
    # Setup Registry
    registry = ToolRegistry()
    broken_tool = BrokenTool()
    registry.register(broken_tool)
    
    # Mock ToolRuntime - let it propagate the error
    mock_runtime = AsyncMock()
    mock_runtime.execute = AsyncMock(return_value={
        "result": None,
        "error": "System Failure"
    })
    
    # Mock PromptBuilder
    mock_builder = MagicMock()
    mock_builder.build_messages = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Call broken tool"}
    ])
    mock_builder.append_tool_result = MagicMock(side_effect=lambda msgs, call_id, result: 
        msgs + [{"role": "tool", "tool_call_id": call_id, "content": str(result.get("result", ""))}]
    )
    
    # Mock SessionStore
    mock_session_store = MagicMock()
    mock_session = MagicMock()
    mock_session.data = {}
    mock_session_store.get_or_create = MagicMock(return_value=mock_session)
    
    # Mock LLM - tries to call broken tool
    mock_llm = MagicMock()
    async def response(*args, **kwargs):
        yield {
            "delta": "",
            "tool_calls": [
                {
                    "id": "err_1",
                    "function": {
                        "name": "broken_tool",
                        "arguments": '{"arg": "x"}'
                    }
                }
            ],
            "finish_reason": "tool_calls"
        }
    
    mock_llm.stream = MagicMock(return_value=response())
    
    # Create Orchestrator
    orchestrator = Orchestrator(
        llm=mock_llm,
        tool_registry=registry,
        tool_runtime=mock_runtime,
        prompt_builder=mock_builder,
        session_store=mock_session_store,
        max_tool_iterations=5
    )
    
    # Run and collect events
    events = []
    async for event in orchestrator.stream_message(
        session_id="sess_fail",
        content="Call broken tool",
        metadata={"provider": "openai", "model": "gpt-4"}
    ):
        events.append(event)
    
    # Assertions
    tool_result_events = [e for e in events if e.type == "tool_result"]
    error_events = [e for e in events if e.type == "error"]
    
    # Tool execution should emit result with error
    assert len(tool_result_events) >= 1, "Expected tool_result event"
    result_data = tool_result_events[0].data
    assert result_data.get("result", {}).get("error") == "System Failure", "Expected error in tool result"
    
    # Should also emit error event (fail-closed)
    assert len(error_events) == 1, "Expected error event for fail-closed"
    assert "Tool error" in error_events[0].error, "Expected 'Tool error' in error message"
    
    print("✅ Fail-Closed Test Passed!")


@pytest.mark.asyncio
async def test_tool_safety_max_iterations():
    """Test max iteration limit (Infinite Loop Guard)"""
    # Setup Registry
    registry = ToolRegistry()
    ping_tool = PingTool()
    registry.register(ping_tool)
    
    # Mock ToolRuntime
    mock_runtime = AsyncMock()
    mock_runtime.execute = AsyncMock(return_value={
        "result": "pong",
        "error": None
    })
    
    # Mock PromptBuilder
    mock_builder = MagicMock()
    mock_builder.build_messages = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Ping forever"}
    ])
    mock_builder.append_tool_result = MagicMock(side_effect=lambda msgs, call_id, result: 
        msgs + [{"role": "tool", "tool_call_id": call_id, "content": str(result.get("result", ""))}]
    )
    
    # Mock SessionStore
    mock_session_store = MagicMock()
    mock_session = MagicMock()
    mock_session.data = {}
    mock_session_store.get_or_create = MagicMock(return_value=mock_session)
    
    # Mock LLM - keeps calling 'ping' forever
    mock_llm = MagicMock()
    async def infinite_response(*args, **kwargs):
        yield {
            "delta": "",
            "tool_calls": [
                {
                    "id": "inf_1",
                    "function": {
                        "name": "ping",
                        "arguments": '{"arg": "x"}'
                    }
                }
            ],
            "finish_reason": "tool_calls"
        }
    
    # Return the same infinite response every time
    mock_llm.stream = MagicMock(side_effect=lambda *args, **kwargs: infinite_response())
    
    # Create Orchestrator with max_tool_iterations=2
    orchestrator = Orchestrator(
        llm=mock_llm,
        tool_registry=registry,
        tool_runtime=mock_runtime,
        prompt_builder=mock_builder,
        session_store=mock_session_store,
        max_tool_iterations=2  # Low limit for testing
    )
    
    # Run and collect events
    events = []
    async for event in orchestrator.stream_message(
        session_id="sess_loop",
        content="Ping forever",
        metadata={"provider": "openai", "model": "gpt-4"}
    ):
        events.append(event)
    
    # Assertions
    tool_call_events = [e for e in events if e.type == "tool_call"]
    error_events = [e for e in events if e.type == "error"]
    
    # Should stop after max_tool_iterations (2 iterations)
    assert len(tool_call_events) == 2, f"Expected 2 tool_call events, got {len(tool_call_events)}"
    
    # Should emit error about max iterations
    assert len(error_events) == 1, "Expected 1 error event"
    assert "Max tool iterations" in error_events[0].error, "Expected 'Max tool iterations' in error"
    
    print("✅ Max Iterations Test Passed!")
    print(f"   Tool calls before abort: {len(tool_call_events)}")
    print(f"   Error message: {error_events[0].error}")
