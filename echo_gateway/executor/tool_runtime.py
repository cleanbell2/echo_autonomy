"""
Tool Runtime — Phase 5

Executes tools with sandbox boundary.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from .tool_registry import Tool


class ToolRuntime:
    """
    Tool execution runtime.

    Provides sandbox boundary for tool execution.
    """

    async def execute(
        self, *, tool: Tool, arguments: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """
        Execute tool with arguments.

        Returns:
            {"result": Any, "error": str | None}

        Fail-closed: tool exceptions → error dict
        """
        try:
            # Validate arguments against schema (basic check)
            self._validate_args(tool, arguments)

            # Execute tool
            result = await tool.run(arguments=arguments, session_id=session_id)

            return result

        except Exception as e:
            # Fail-closed: return error dict
            return {"result": None, "error": f"Tool execution error: {str(e)}"}

    def _validate_args(self, tool: Tool, arguments: Dict[str, Any]) -> None:
        """
        Validate arguments against tool schema.

        Raises ValueError if validation fails.
        """
        schema = tool.spec.input_schema
        required = schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in arguments:
                raise ValueError(f"Missing required argument: {field}")

        # Check types (basic validation)
        properties = schema.get("properties", {})
        for key, value in arguments.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Argument {key} must be string")
                elif expected_type == "number" and not isinstance(
                    value, (int, float)
                ):
                    raise ValueError(f"Argument {key} must be number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Argument {key} must be boolean")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"Argument {key} must be object")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Argument {key} must be array")
