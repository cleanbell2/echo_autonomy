"""
Test tool runtime — Phase 5
"""

import pytest

from echo_gateway.executor.tool_registry import ToolSpec
from echo_gateway.executor.tool_runtime import ToolRuntime


class SuccessTool:
    """Tool that succeeds."""

    spec = ToolSpec(
        name="success_tool",
        description="Always succeeds",
        input_schema={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        },
    )

    async def run(self, *, arguments, session_id):
        return {"result": f"Success: {arguments['value']}", "error": None}


class ErrorTool:
    """Tool that raises exception."""

    spec = ToolSpec(
        name="error_tool",
        description="Always fails",
        input_schema={"type": "object", "properties": {}, "required": []},
    )

    async def run(self, *, arguments, session_id):
        raise ValueError("Tool error")


@pytest.mark.asyncio
async def test_tool_runtime_execute_success():
    """Execute tool successfully."""
    runtime = ToolRuntime()
    tool = SuccessTool()
    result = await runtime.execute(
        tool=tool, arguments={"value": "test"}, session_id="test-session"
    )
    assert result["error"] is None
    assert "Success: test" in result["result"]


@pytest.mark.asyncio
async def test_tool_runtime_execute_missing_required_arg():
    """Execute tool with missing required argument → error."""
    runtime = ToolRuntime()
    tool = SuccessTool()
    result = await runtime.execute(tool=tool, arguments={}, session_id="test-session")
    assert result["error"] is not None
    assert "Missing required argument" in result["error"]


@pytest.mark.asyncio
async def test_tool_runtime_execute_tool_exception():
    """Execute tool that raises exception → error dict."""
    runtime = ToolRuntime()
    tool = ErrorTool()
    result = await runtime.execute(tool=tool, arguments={}, session_id="test-session")
    assert result["error"] is not None
    assert "Tool execution error" in result["error"]


@pytest.mark.asyncio
async def test_tool_runtime_execute_type_validation():
    """Execute tool with wrong argument type → error."""
    runtime = ToolRuntime()
    tool = SuccessTool()
    result = await runtime.execute(
        tool=tool, arguments={"value": 123}, session_id="test-session"
    )
    assert result["error"] is not None
    assert "must be string" in result["error"]
