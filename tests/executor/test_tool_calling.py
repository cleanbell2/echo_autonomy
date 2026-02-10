"""
Tests for tool calling protocol and translation.
"""
import pytest
from echo_gateway.executor.tool_calling import (
    ToolCall,
    ToolResult,
    ToolCallTranslator,
)


def test_tool_call_creation():
    """Test ToolCall dataclass creation."""
    call = ToolCall(
        id="call_123",
        name="get_weather",
        arguments={"city": "Seoul"}
    )
    
    assert call.id == "call_123"
    assert call.name == "get_weather"
    assert call.arguments["city"] == "Seoul"


def test_tool_result_creation():
    """Test ToolResult dataclass creation."""
    result = ToolResult(
        call_id="call_123",
        result={"temperature": 25},
        duration_ms=150.5
    )
    
    assert result.call_id == "call_123"
    assert result.result["temperature"] == 25
    assert result.error is None
    assert result.duration_ms == 150.5


def test_to_openai_tools():
    """Test internal schema → OpenAI function format."""
    internal_tools = [
        {
            "name": "get_weather",
            "description": "Get weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                }
            }
        }
    ]
    
    openai_tools = ToolCallTranslator.to_openai_tools(internal_tools)
    
    assert len(openai_tools) == 1
    assert openai_tools[0]["type"] == "function"
    assert openai_tools[0]["function"]["name"] == "get_weather"
    assert openai_tools[0]["function"]["parameters"]["type"] == "object"


def test_to_anthropic_tools():
    """Test internal schema → Anthropic tool format."""
    internal_tools = [
        {
            "name": "get_weather",
            "description": "Get weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                }
            }
        }
    ]
    
    anthropic_tools = ToolCallTranslator.to_anthropic_tools(internal_tools)
    
    assert len(anthropic_tools) == 1
    assert anthropic_tools[0]["name"] == "get_weather"
    assert anthropic_tools[0]["input_schema"]["type"] == "object"


def test_empty_tools():
    """Test handling of empty tool lists."""
    assert ToolCallTranslator.to_openai_tools([]) == []
    assert ToolCallTranslator.to_anthropic_tools([]) == []
    assert ToolCallTranslator.to_openai_tools(None) == []
    assert ToolCallTranslator.to_anthropic_tools(None) == []
