"""
Tool Registry — Phase 5

Tool registration, lookup, and schema enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass(frozen=True)
class ToolSpec:
    """
    Tool specification.

    - name: unique tool identifier
    - description: human-readable description
    - input_schema: JSON Schema for tool arguments
    """

    name: str
    description: str
    input_schema: Dict[str, Any]


class Tool(Protocol):
    """
    Tool protocol.

    All tools must implement:
    - spec: ToolSpec with schema
    - run: async execution method
    """

    spec: ToolSpec

    async def run(
        self, *, arguments: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """
        Run tool with arguments.

        Returns:
            {"result": Any, "error": str | None}
        """
        ...


class ToolRegistry:
    """
    Tool registry for registration and lookup.

    Fail-closed: unknown tools → ValueError
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.spec.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.spec.name}")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> Tool:
        """
        Get tool by name.

        Raises ValueError if not found (fail-closed).
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_specs(self) -> List[ToolSpec]:
        """List all registered tool specs."""
        return [t.spec for t in self._tools.values()]

    def to_llm_tools(self) -> List[Dict[str, Any]]:
        """
        Convert tools to LLM-compatible format.

        OpenAI-compatible tool spec format.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t.spec.name,
                    "description": t.spec.description,
                    "parameters": t.spec.input_schema,
                },
            }
            for t in self._tools.values()
        ]
