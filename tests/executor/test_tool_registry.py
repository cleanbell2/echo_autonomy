"""
Test tool registry — Phase 5
"""

import pytest

from echo_gateway.executor.tool_registry import Tool, ToolRegistry, ToolSpec


class FakeTool:
    """Fake tool for testing."""

    def __init__(self, name: str):
        self.spec = ToolSpec(
            name=name,
            description=f"Fake tool {name}",
            input_schema={"type": "object", "properties": {}, "required": []},
        )

    async def run(self, *, arguments, session_id):
        return {"result": f"Fake {self.spec.name}", "error": None}


def test_tool_registry_register():
    """Register tool successfully."""
    registry = ToolRegistry()
    tool = FakeTool("test_tool")
    registry.register(tool)
    assert registry.get("test_tool") == tool


def test_tool_registry_duplicate_raises():
    """Registering duplicate tool raises ValueError."""
    registry = ToolRegistry()
    tool = FakeTool("test_tool")
    registry.register(tool)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool)


def test_tool_registry_get_unknown_raises():
    """Getting unknown tool raises ValueError."""
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.get("unknown_tool")


def test_tool_registry_list_specs():
    """list_specs returns all registered tool specs."""
    registry = ToolRegistry()
    tool1 = FakeTool("tool1")
    tool2 = FakeTool("tool2")
    registry.register(tool1)
    registry.register(tool2)
    specs = registry.list_specs()
    assert len(specs) == 2
    assert any(s.name == "tool1" for s in specs)
    assert any(s.name == "tool2" for s in specs)


def test_tool_registry_to_llm_tools():
    """to_llm_tools converts to LLM-compatible format."""
    registry = ToolRegistry()
    tool = FakeTool("test_tool")
    registry.register(tool)
    llm_tools = registry.to_llm_tools()
    assert len(llm_tools) == 1
    assert llm_tools[0]["type"] == "function"
    assert llm_tools[0]["function"]["name"] == "test_tool"
    assert "description" in llm_tools[0]["function"]
    assert "parameters" in llm_tools[0]["function"]
