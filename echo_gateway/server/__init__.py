"""
Echo Gateway Server — Phase 4

FastAPI application factory + HTTP/WS routes.
"""

from .app import create_app

__all__ = ["create_app"]
