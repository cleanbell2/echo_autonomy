import pytest
from unittest.mock import AsyncMock, MagicMock
from echo_gateway.executor.orchestrator import Orchestrator
from echo_gateway.executor.tool_registry import ToolRegistry, ToolSpec
from echo_gateway.executor.tool_calling import ToolCall
from echo_gateway.executor.streaming import StreamEvent
from echo_gateway.session.store import SessionStore


# 1. Dummy Tool (following Tool Protocol)
class WeatherTool:
    spec = ToolSpec(
        name="get_weather",
        description="Get weather for a city",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    )
    
    async def run(self, *, arguments: dict, session_id: str):
        city = arguments.get("city", "Unknown")
        return {"result": f"Weather in {city} is Sunny", "error": None}


@pytest.mark.asyncio
async def test_tool_loop_integration():
    # Setup
    registry = ToolRegistry()
    weather_tool = WeatherTool()
    registry.register(weather_tool)
@pytest.mark.asyncio
async def test_tool_loop_integration():
    # Setup Registry
    registry = ToolRegistry()
    weather_tool = WeatherTool()
    registry.register(weather_tool)
    
    # Mock ToolRuntime
    mock_runtime = AsyncMock()
    mock_runtime.execute = AsyncMock(return_value={
        "result": "Weather in Seoul is Sunny",
        "error": None
    })
    
    # Mock PromptBuilder
    mock_builder = MagicMock()
    mock_builder.build_messages = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the weather in Seoul?"}
    ])
    mock_builder.append_tool_result = MagicMock(side_effect=lambda msgs, call_id, result: 
        msgs + [{"role": "tool", "tool_call_id": call_id, "content": str(result.get("result", ""))}]
    )
    
    # Mock SessionStore
    mock_session_store = MagicMock()
    mock_session = MagicMock()
    mock_session.data = {}
    mock_session_store.get_or_create = MagicMock(return_value=mock_session)
    
    # Mock LLM with two-turn interaction
    mock_llm = MagicMock()
    
    # Turn 1: LLM requests tool call
    async def stream_turn_1(*args, **kwargs):
        yield {
            "delta": "",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "Seoul"}'
                    }
                }
            ],
            "finish_reason": "tool_calls"
        }
    
    # Turn 2: LLM provides final answer after tool result
    async def stream_turn_2(*args, **kwargs):
        # Verify tool result was injected
        messages = kwargs.get("messages", [])
        assert any(msg.get("role") == "tool" for msg in messages), "Tool result not injected!"
        
        yield {"delta": "The weather", "finish_reason": None}
        yield {"delta": " in Seoul is Sunny.", "finish_reason": None}
        yield {"delta": "", "finish_reason": "stop"}
    
    # Setup mock - note we need to return the async generator, not call it
    call_count = [0]  # Use list to allow mutation in nested function
    def stream_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return stream_turn_1(*args, **kwargs)
        else:
            return stream_turn_2(*args, **kwargs)
    
    mock_llm.stream = MagicMock(side_effect=stream_side_effect)
    
    # Create Orchestrator
    orchestrator = Orchestrator(
        llm=mock_llm,
        tool_registry=registry,
        tool_runtime=mock_runtime,
        prompt_builder=mock_builder,
        session_store=mock_session_store,
        max_tool_iterations=5
    )
    
    # Run stream_message
    events = []
    async for event in orchestrator.stream_message(
        session_id="test_session",
        content="What's the weather in Seoul?",
        metadata={"provider": "openai", "model": "gpt-4"}
    ):
        events.append(event)
    
    # Assertions
    tool_call_events = [e for e in events if e.type == "tool_call"]
    tool_result_events = [e for e in events if e.type == "tool_result"]
    delta_events = [e for e in events if e.type == "delta"]
    final_events = [e for e in events if e.type == "final"]
    
    # Verify tool call was emitted
    assert len(tool_call_events) >= 1, "No tool_call events emitted"
    
    # Verify tool result was emitted
    assert len(tool_result_events) >= 1, "No tool_result events emitted"
    assert "Sunny" in str(tool_result_events[0].data.get("result", ""))
    
    # Verify final answer included deltas
    assert len(delta_events) > 0, "No delta events emitted"
    
    # Verify final event
    assert len(final_events) == 1, "Expected exactly 1 final event"
    
    # Verify tool was actually executed
    assert mock_runtime.execute.called, "Tool runtime was not called"
    
    print("✅ Loop Test Passed!")
    print(f"   Events: {len(events)} total")
    print(f"   - tool_call: {len(tool_call_events)}")
    print(f"   - tool_result: {len(tool_result_events)}")
    print(f"   - delta: {len(delta_events)}")
    print(f"   - final: {len(final_events)}")
