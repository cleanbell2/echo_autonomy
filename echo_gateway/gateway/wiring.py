"""
Gateway Wiring — Phase 7.2

Orchestrator dependency injection with real LLM factory.
"""

from __future__ import annotations

from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor import (
    Orchestrator,
    PromptBuilder,
    ToolRegistry,
    ToolRuntime,
)
from echo_gateway.executor.llm_factory import build_llm_client
from echo_gateway.session import SessionStore


def create_orchestrator(session_store: SessionStore) -> Orchestrator:
    """
    Create orchestrator with LLM from config/factory.

    Phase 7.2: Uses LLMConfig + Factory pattern for dynamic LLM selection.
    - Provider: fake (default), openai, anthropic
    - Config loaded from environment variables

    Args:
        session_store: Session store instance

    Returns:
        Configured Orchestrator instance
    """
    # LLM client (from config + factory)
    cfg = LLMConfig.from_env()
    llm = build_llm_client(cfg)

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
