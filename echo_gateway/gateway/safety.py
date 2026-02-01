"""
Safety check stub — Phase 4

Placeholder for BCDSI integration.
Future phases will integrate real safety/moderation checks.
"""

from __future__ import annotations

from typing import Any, Dict

from .pipeline import SafetyDecision


def stub_safety_check(stage: str, payload: Dict[str, Any]) -> SafetyDecision:
    """
    Stub safety check for Phase 4.

    Always returns ALLOW.
    Future phases will integrate BCDSI or other safety layers.
    """
    return SafetyDecision(level="ALLOW", reason="Phase 4 stub — no real checks")
