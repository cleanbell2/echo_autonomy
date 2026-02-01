"""
Echo Gateway Executor — Phase 5

Real executor with LLM + tools + streaming.
"""

from .fake_llm_client import FakeLLMClient
from .interface import ExecResult, Executor, Status
from .llm_client import LLMClient
from .local import LocalExecutor
from .orchestrator import Orchestrator
from .prompt_builder import PromptBuilder
from .streaming import StreamEvent, StreamEventType
from .tool_registry import Tool, ToolRegistry, ToolSpec
from .tool_runtime import ToolRuntime

__all__ = [
    "Executor",
    "ExecResult",
    "Status",
    "LocalExecutor",
    "LLMClient",
    "FakeLLMClient",
    "Orchestrator",
    "PromptBuilder",
    "StreamEvent",
    "StreamEventType",
    "Tool",
    "ToolRegistry",
    "ToolSpec",
    "ToolRuntime",
]
