"""
SessionStore — Phase 4 in-memory implementation

get_or_create: fetch or create session, update last_seen
sweep: remove idle sessions exceeding TTL
"""

from __future__ import annotations

import time
from typing import Dict

from .model import SessionState


class SessionStore:
    """
    In-memory session store with TTL-based expiration.

    Methods:
    - get_or_create(session_id): fetch or create, update last_seen
    - sweep(): remove sessions idle beyond ttl_seconds
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        """
        Fetch existing session or create new.

        Updates last_seen to current time.
        """
        s = self._sessions.get(session_id)
        if s is None:
            s = SessionState(session_id=session_id)
            self._sessions[session_id] = s
        s.last_seen = time.time()
        return s

    def sweep(self) -> int:
        """
        Remove sessions idle beyond TTL.

        Returns number of sessions removed.
        """
        now = time.time()
        to_del = [
            sid
            for sid, s in self._sessions.items()
            if (now - s.last_seen) > self._ttl
        ]
        for sid in to_del:
            del self._sessions[sid]
        return len(to_del)
