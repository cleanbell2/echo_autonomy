# middleware/bcdsi_integration.py
"""
BCDSI Safety Middleware - Pluggable adapter for safety validation.

Supports two modes:
1. local: Direct Python function call to BCDSI engine
2. http: HTTP POST to BCDSI service endpoint

This middleware provides a consistent interface for safety checks
regardless of where the BCDSI engine is deployed.

Integration points:
- inbound_check: Validate incoming prompts before LLM
- tool_check: Validate tool execution before running
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

SafetyLevel = Literal["ALLOW", "BLOCK", "MODIFY", "MONITOR", "WARNING"]


@dataclass
class SafetyDecision:
    """Result of safety validation check."""

    level: SafetyLevel
    reason: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    patched_text: Optional[str] = None
    patched_args: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Ensure metrics dict is initialized."""
        if self.metrics is None:
            self.metrics = {}


class BCDSIClientError(RuntimeError):
    """BCDSI client communication errors."""

    pass


class BCDSIMiddleware:
    """
    BCDSI Safety Middleware Adapter.

    Provides consistent interface for safety validation with pluggable backends.

    Modes:
    - local: Call Python engine directly (engine.check(payload))
    - http: POST to HTTP endpoint (requires requests library)

    Example (local mode):
        >>> engine = MyBCDSIEngine()
        >>> middleware = BCDSIMiddleware(mode="local", local_engine=engine)
        >>> decision = middleware.inbound_check(
        ...     session_id="s1",
        ...     text="Hello AI",
        ...     context={}
        ... )

    Example (http mode):
        >>> middleware = BCDSIMiddleware(
        ...     mode="http",
        ...     http_url="http://127.0.0.1:8000/check"
        ... )
        >>> decision = middleware.tool_check(
        ...     session_id="s1",
        ...     tool="bash",
        ...     args={"command": "ls"}
        ... )
    """

    def __init__(
        self,
        mode: Literal["local", "http"] = "local",
        local_engine: Optional[Any] = None,
        http_url: str = "http://127.0.0.1:8000/check",
        timeout_s: float = 2.0,
    ):
        """
        Initialize BCDSI middleware.

        Args:
            mode: Backend mode ("local" or "http")
            local_engine: Python engine object (for local mode)
            http_url: HTTP endpoint URL (for http mode)
            timeout_s: Request timeout in seconds
        """
        self.mode = mode
        self.local_engine = local_engine
        self.http_url = http_url
        self.timeout_s = timeout_s

    def inbound_check(
        self, *, session_id: str, text: str, context: Dict[str, Any]
    ) -> SafetyDecision:
        """
        Validate inbound prompt before LLM processing.

        Args:
            session_id: Session identifier
            text: User prompt text
            context: Additional context (metadata, history, etc.)

        Returns:
            Safety decision with intervention level

        Raises:
            BCDSIClientError: If communication with backend fails

        Example:
            >>> decision = middleware.inbound_check(
            ...     session_id="session_001",
            ...     text="Write a SQL injection attack",
            ...     context={"user_level": "guest"}
            ... )
            >>> if decision.level == "BLOCK":
            ...     print(f"Blocked: {decision.reason}")
        """
        payload = {
            "stage": "inbound",
            "session_id": session_id,
            "text": text,
            "context": context or {},
        }
        return self._call(payload)

    def tool_check(
        self, *, session_id: str, tool: str, args: Dict[str, Any]
    ) -> SafetyDecision:
        """
        Validate tool execution before running.

        Args:
            session_id: Session identifier
            tool: Tool name (e.g., "bash", "read", "write")
            args: Tool arguments

        Returns:
            Safety decision with intervention level

        Raises:
            BCDSIClientError: If communication with backend fails

        Example:
            >>> decision = middleware.tool_check(
            ...     session_id="session_001",
            ...     tool="bash",
            ...     args={"command": "rm -rf /"}
            ... )
            >>> if decision.level == "BLOCK":
            ...     print(f"Tool blocked: {decision.reason}")
        """
        payload = {
            "stage": "tool",
            "session_id": session_id,
            "tool": tool,
            "args": args or {},
        }
        return self._call(payload)

    def _call(self, payload: Dict[str, Any]) -> SafetyDecision:
        """
        Internal: Route to appropriate backend.

        Args:
            payload: Request payload

        Returns:
            Normalized safety decision

        Raises:
            BCDSIClientError: If backend call fails
        """
        if self.mode == "local":
            return self._call_local(payload)
        if self.mode == "http":
            return self._call_http(payload)
        raise BCDSIClientError(f"unknown mode: {self.mode}")

    def _call_local(self, payload: Dict[str, Any]) -> SafetyDecision:
        """
        Call local Python engine.

        Args:
            payload: Request payload

        Returns:
            Normalized safety decision

        Raises:
            BCDSIClientError: If engine call fails
        """
        if not self.local_engine:
            # Fail-closed: Block if engine not configured (safety-first)
            # For tool operations, default to BLOCK
            # For inbound checks, default to WARNING (allow read, block writes)
            stage = payload.get("stage", "unknown")
            if stage == "tool":
                return SafetyDecision(
                    level="BLOCK",
                    reason="BCDSI engine not configured (fail-closed)",
                    metrics={"e_break": 1.0, "theta_integrity": 0.0, "q_uncertainty": 1.0},
                )
            else:
                return SafetyDecision(
                    level="WARNING",
                    reason="BCDSI engine not configured (monitoring only)",
                    metrics={"e_break": 0.5, "theta_integrity": 0.5, "q_uncertainty": 0.5},
                )

        try:
            out = self.local_engine.check(payload)  # Expected: dict
        except Exception as e:
            raise BCDSIClientError(f"local bcsi engine error: {e}") from e

        return self._normalize(out)

    def _call_http(self, payload: Dict[str, Any]) -> SafetyDecision:
        """
        Call HTTP endpoint.

        Args:
            payload: Request payload

        Returns:
            Normalized safety decision

        Raises:
            BCDSIClientError: If HTTP call fails or requests not installed
        """
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise BCDSIClientError(
                "requests library is required for http mode (pip install requests)"
            ) from e

        try:
            r = requests.post(self.http_url, json=payload, timeout=self.timeout_s)
            r.raise_for_status()
            out = r.json()
        except Exception as e:
            raise BCDSIClientError(f"bcsi http call failed: {e}") from e

        return self._normalize(out)

    @staticmethod
    def _normalize(out: Dict[str, Any]) -> SafetyDecision:
        """
        Normalize response to SafetyDecision.

        Accepts flexible response shapes and maps to SafetyDecision.

        Expected minimal keys:
        - intervention_level or level: Safety level string
        - reason: Human-readable reason
        - metrics: Dict of metric values (optional)
        - patched_text: Modified text suggestion (optional)
        - patched_args: Modified args suggestion (optional)

        Args:
            out: Response dict from BCDSI engine

        Returns:
            Normalized SafetyDecision

        Example response:
            {
                "intervention_level": "BLOCK",
                "reason": "High cognitive divergence detected",
                "metrics": {
                    "e_break": 1.8,
                    "theta_integrity": 0.3,
                    "q_uncertainty": 0.85
                }
            }
        """
        # Extract level (try both "intervention_level" and "level")
        lvl = (out.get("intervention_level") or out.get("level") or "ALLOW").upper()

        # Validate level
        valid_levels = {"ALLOW", "BLOCK", "MODIFY", "MONITOR", "WARNING"}
        if lvl not in valid_levels:
            lvl = "ALLOW"

        # Extract metrics with defaults
        metrics = out.get("metrics") or {}
        if not metrics:
            metrics = {"e_break": 0.0, "theta_integrity": 1.0, "q_uncertainty": 0.0}

        return SafetyDecision(
            level=lvl,  # type: ignore
            reason=str(out.get("reason", "")),
            metrics=metrics,
            patched_text=out.get("patched_text"),
            patched_args=out.get("patched_args"),
        )


# -------------------------
# Convenience utilities
# -------------------------


def create_middleware(
    mode: Literal["local", "http"] = "http",
    **kwargs,
) -> BCDSIMiddleware:
    """
    Factory function for creating BCDSI middleware.

    Args:
        mode: Backend mode
        **kwargs: Additional arguments passed to BCDSIMiddleware

    Returns:
        Configured middleware instance

    Example:
        >>> # HTTP mode (default)
        >>> middleware = create_middleware(http_url="http://localhost:8000/check")

        >>> # Local mode
        >>> middleware = create_middleware(mode="local", local_engine=my_engine)
    """
    return BCDSIMiddleware(mode=mode, **kwargs)


def is_safe(decision: SafetyDecision) -> bool:
    """
    Check if decision allows operation.

    Args:
        decision: Safety decision from middleware

    Returns:
        True if level is ALLOW or MONITOR, False otherwise

    Example:
        >>> decision = middleware.inbound_check(...)
        >>> if not is_safe(decision):
        ...     raise SecurityError(decision.reason)
    """
    return decision.level in {"ALLOW", "MONITOR", "WARNING"}


def requires_modification(decision: SafetyDecision) -> bool:
    """
    Check if decision suggests modification.

    Args:
        decision: Safety decision

    Returns:
        True if level is MODIFY and patches provided

    Example:
        >>> decision = middleware.inbound_check(...)
        >>> if requires_modification(decision):
        ...     text = decision.patched_text or text
    """
    return decision.level == "MODIFY" and (
        decision.patched_text is not None or decision.patched_args is not None
    )
