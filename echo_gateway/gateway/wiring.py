"""
Gateway Wiring — Phase 6

Orchestrator dependency injection and initialization.
"""

from __future__ import annotations

from echo_gateway.executor import (
    FakeLLMClient,
    Orchestrator,
    PromptBuilder,
    ToolRegistry,
    ToolRuntime,
)
from echo_gateway.session import SessionStore


def create_orchestrator(session_store: SessionStore) -> Orchestrator:
    """
    Create orchestrator with default configuration.

    Phase 6: Uses FakeLLMClient for testing.
    Phase 7+: Replace with real LLM adapters (OpenAI, Anthropic).

    Args:
        session_store: Session store instance

    Returns:
        Configured Orchestrator instance
    """
    # LLM client (fake for Phase 6)
    llm = FakeLLMClient(mode="echo")

    # Tool system
    tool_registry = ToolRegistry()
    tool_runtime = ToolRuntime()

    # Register default tools (if any)
    # Example: tool_registry.register(CalculatorTool())

    # Prompt builder
    prompt_builder = PromptBuilder(
        system_prompt="You are a helpful assistant. Respond concisely."
    )

    return Orchestrator(
        llm=llm,
        tool_registry=tool_registry,
        tool_runtime=tool_runtime,
        prompt_builder=prompt_builder,
        session_store=session_store,
        max_tool_iterations=5,
    )
