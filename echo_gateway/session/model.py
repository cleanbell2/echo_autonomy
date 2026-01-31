"""
SessionState model — Phase 4

Tracks session lifecycle: created_at, last_seen, arbitrary data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SessionState:
    """
    Represents a single session.

    - session_id: unique session identifier
    - created_at: epoch timestamp (seconds)
    - last_seen: epoch timestamp (seconds), updated on activity
    - data: arbitrary session-scoped key-value store
    """

    session_id: str
    created_at: float = field(default_factory=lambda: time.time())
    last_seen: float = field(default_factory=lambda: time.time())
    data: Dict[str, Any] = field(default_factory=dict)
