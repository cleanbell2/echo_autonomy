"""
Tool calling protocol and translation layer.

Provides unified tool call/result format across LLM providers:
- OpenAI function calling
- Anthropic tool use
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolCall:
    """Unified tool call format across providers."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Unified tool result format."""
    call_id: str
    result: Any
    error: Optional[str] = None
    duration_ms: float = 0.0


class ToolCallTranslator:
    """Translate provider-specific tool calls to unified format."""
    
    @staticmethod
    def from_openai(tool_call_obj) -> ToolCall:
        """
        Translate OpenAI function calling to ToolCall.
        
        OpenAI format:
        {
          "id": "call_123",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": '{"city": "Seoul"}'
          }
        }
        """
        try:
            args = tool_call_obj.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            
            return ToolCall(
                id=tool_call_obj.id,
                name=tool_call_obj.function.name,
                arguments=args
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in OpenAI tool arguments: {tool_call_obj.function.arguments}"
            ) from e
    
    @staticmethod
    def from_anthropic(tool_use_block) -> ToolCall:
        """
        Translate Anthropic tool use to ToolCall.
        
        Anthropic format:
        {
          "type": "tool_use",
          "id": "toolu_123",
          "name": "get_weather",
          "input": {"city": "Seoul"}
        }
        """
        return ToolCall(
            id=tool_use_block.id,
            name=tool_use_block.name,
            arguments=tool_use_block.input
        )
    
    @staticmethod
    def to_openai_tools(tools: list) -> list:
        """
        Convert internal tool schema to OpenAI function format.
        
        Internal format:
        {
          "name": "get_weather",
          "description": "Get weather",
          "input_schema": {"type": "object", "properties": {...}}
        }
        
        OpenAI format:
        {
          "type": "function",
          "function": {
            "name": "get_weather",
            "description": "Get weather",
            "parameters": {"type": "object", "properties": {...}}
          }
        }
        """
        if not tools:
            return []
        
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t["input_schema"]
                }
            }
            for t in tools
        ]
    
    @staticmethod
    def to_anthropic_tools(tools: list) -> list:
        """
        Convert internal tool schema to Anthropic tool format.
        
        Anthropic format:
        {
          "name": "get_weather",
          "description": "Get weather",
          "input_schema": {"type": "object", "properties": {...}}
        }
        """
        if not tools:
            return []
        
        return [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t["input_schema"]
            }
            for t in tools
        ]
