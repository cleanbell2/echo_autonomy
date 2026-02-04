"""
FastAPI dependencies — Phase 6

Provides session store, orchestrator, executor, safety check via dependency injection.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Request

from echo_gateway.executor import Orchestrator
from echo_gateway.executor.local import LocalExecutor
from echo_gateway.gateway.pipeline import SafetyCheck
from echo_gateway.gateway.wiring import create_orchestrator
from echo_gateway.session.store import SessionStore


def get_session_store(request: Request) -> SessionStore:
    """Dependency: session store."""
    if not hasattr(request.app.state, "session_store"):
        # Initialize on first access (for tests)
        request.app.state.session_store = SessionStore(ttl_seconds=3600)
    return request.app.state.session_store


def get_orchestrator(request: Request) -> Orchestrator:
    """
    Dependency: orchestrator (Phase 6).

    Creates orchestrator on first access and caches in app state.
    """
    if not hasattr(request.app.state, "orchestrator"):
        session_store = get_session_store(request)
        request.app.state.orchestrator = create_orchestrator(session_store)
    return request.app.state.orchestrator


def get_executor(request: Request) -> LocalExecutor:
    """Dependency: executor (Phase 4 compatibility)."""
    return request.app.state.executor


def get_safety_check(request: Request) -> SafetyCheck:
    """Dependency: safety check callable."""
    return request.app.state.safety_check
