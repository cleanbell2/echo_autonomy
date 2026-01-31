"""
Echo Gateway Pipeline — Phase 4

Orchestrates: envelope → validate → parse → safety → execute → respond
"""

from .pipeline import handle_inbound

__all__ = ["handle_inbound"]
