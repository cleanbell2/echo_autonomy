"""
Echo Gateway WebSocket — Phase 4

/ws endpoint for bi-directional JSON-RPC style communication.
"""

from .router import router

__all__ = ["router"]
