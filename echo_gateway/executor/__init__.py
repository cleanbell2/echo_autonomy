"""
Echo Gateway Executor — Phase 4

Defines the contract for message/tool/status execution.
Phase 4 ships with LocalExecutor (stub implementation).
Future phases can integrate real LLM backends.
"""

from .interface import Executor, ExecResult, Status
from .local import LocalExecutor

__all__ = ["Executor", "ExecResult", "Status", "LocalExecutor"]
