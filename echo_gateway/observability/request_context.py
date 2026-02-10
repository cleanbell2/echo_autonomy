"""
Request context management for observability.

Provides thread-safe request tracking with:
- request_id propagation
- provider/model tracking
- tool call audit logging
- token usage tracking
"""
import time
import uuid
import contextvars
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class ToolCallAudit:
    """Audit record for a single tool execution."""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    duration_ms: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RequestContextData:
    """Context data for a single request."""
    request_id: str
    provider: str = "unknown"
    model: str = "unknown"
    start_time: float = field(default_factory=time.time)
    tool_calls: List[ToolCallAudit] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt": 0,
        "completion": 0,
        "total": 0
    })
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - self.start_time) * 1000


# Context variable for storing request context
_request_context = contextvars.ContextVar("request_context", default=None)


class RequestContext:
    """
    Manage request context for observability.
    
    Usage:
        ctx = RequestContext.begin(provider="openai", model="gpt-4")
        # ... do work ...
        RequestContext.record_tool_call(audit)
        data = RequestContext.get()
    """
    
    @staticmethod
    def begin(
        provider: str = "unknown",
        model: str = "unknown",
        request_id: Optional[str] = None
    ) -> RequestContextData:
        """
        Begin a new request context.
        
        Args:
            provider: LLM provider name
            model: Model name
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            New context data
        """
        ctx = RequestContextData(
            request_id=request_id or str(uuid.uuid4()),
            provider=provider,
            model=model
        )
        _request_context.set(ctx)
        return ctx
    
    @staticmethod
    def get() -> Optional[RequestContextData]:
        """Get current request context."""
        return _request_context.get()
    
    @staticmethod
    def record_tool_call(audit: ToolCallAudit):
        """Record a tool call execution."""
        ctx = RequestContext.get()
        if ctx:
            ctx.tool_calls.append(audit)
    
    @staticmethod
    def record_usage(prompt: int, completion: int):
        """Record token usage."""
        ctx = RequestContext.get()
        if ctx:
            ctx.token_usage["prompt"] += prompt
            ctx.token_usage["completion"] += completion
            ctx.token_usage["total"] += (prompt + completion)
    
    @staticmethod
    def clear():
        """Clear current context."""
        _request_context.set(None)
