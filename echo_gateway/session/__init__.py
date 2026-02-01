"""
Echo Gateway Session Management — Phase 4

In-memory session store with TTL and auto-sweep.
Future phases can add persistence (Redis, DB, etc.).
"""

from .model import SessionState
from .store import SessionStore

__all__ = ["SessionState", "SessionStore"]
