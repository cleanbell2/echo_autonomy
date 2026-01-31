"""
FastAPI dependencies — Phase 4

Provides session store, executor, safety check via dependency injection.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Request

from echo_gateway.executor.local import LocalExecutor
from echo_gateway.gateway.pipeline import SafetyCheck
from echo_gateway.session.store import SessionStore


def get_session_store(request: Request) -> SessionStore:
    """Dependency: session store."""
    return request.app.state.session_store


def get_executor(request: Request) -> LocalExecutor:
    """Dependency: executor."""
    return request.app.state.executor


def get_safety_check(request: Request) -> SafetyCheck:
    """Dependency: safety check callable."""
    return request.app.state.safety_check
