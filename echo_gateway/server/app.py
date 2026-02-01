"""
FastAPI application factory — Phase 4

create_app: wire routes + dependencies + lifecycle
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from echo_gateway.executor.local import LocalExecutor
from echo_gateway.gateway.safety import stub_safety_check
from echo_gateway.session.store import SessionStore

from .deps import get_executor, get_safety_check, get_session_store
from .routes import router as http_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: setup + teardown."""
    # Setup: initialize stores/executors
    app.state.session_store = SessionStore(ttl_seconds=3600)
    app.state.executor = LocalExecutor()
    app.state.safety_check = stub_safety_check
    yield
    # Teardown: cleanup if needed


def create_app() -> FastAPI:
    """
    Create FastAPI application.

    Includes:
    - HTTP routes (/health, /api/message)
    - WS routes (/ws)
    - Dependency injection for session/executor/safety
    """
    app = FastAPI(title="Echo Gateway", lifespan=lifespan)
    app.include_router(http_router)

    # WS router imported separately to avoid circular deps
    from echo_gateway.ws.router import router as ws_router

    app.include_router(ws_router)

    return app
