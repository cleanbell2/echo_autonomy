"""
Tests for observability request context.
"""
import time
import pytest
from echo_gateway.observability import (
    RequestContext,
    RequestContextData,
    ToolCallAudit,
)


def test_request_context_begin():
    """Test starting a new request context."""
    ctx = RequestContext.begin(provider="openai", model="gpt-4")
    
    assert ctx.provider == "openai"
    assert ctx.model == "gpt-4"
    assert ctx.request_id is not None
    assert len(ctx.tool_calls) == 0


def test_request_context_get():
    """Test retrieving current context."""
    RequestContext.begin(provider="anthropic", model="claude-3")
    ctx = RequestContext.get()
    
    assert ctx is not None
    assert ctx.provider == "anthropic"
    assert ctx.model == "claude-3"


def test_request_context_custom_id():
    """Test custom request ID."""
    custom_id = "test-123"
    ctx = RequestContext.begin(request_id=custom_id)
    
    assert ctx.request_id == custom_id


def test_record_tool_call():
    """Test recording tool call audit."""
    RequestContext.begin()
    
    audit = ToolCallAudit(
        call_id="call_1",
        tool_name="test_tool",
        arguments={"x": 1},
        result="success",
        duration_ms=100.0
    )
    
    RequestContext.record_tool_call(audit)
    ctx = RequestContext.get()
    
    assert len(ctx.tool_calls) == 1
    assert ctx.tool_calls[0].tool_name == "test_tool"


def test_record_usage():
    """Test recording token usage."""
    RequestContext.begin()
    
    RequestContext.record_usage(prompt=10, completion=20)
    RequestContext.record_usage(prompt=5, completion=10)
    
    ctx = RequestContext.get()
    assert ctx.token_usage["prompt"] == 15
    assert ctx.token_usage["completion"] == 30
    assert ctx.token_usage["total"] == 45


def test_elapsed_ms():
    """Test elapsed time calculation."""
    ctx = RequestContext.begin()
    time.sleep(0.05)
    
    elapsed = ctx.elapsed_ms()
    assert elapsed >= 50
    assert elapsed < 100


def test_context_isolation():
    """Test that contexts are isolated."""
    RequestContext.begin(provider="openai")
    ctx1 = RequestContext.get()
    
    RequestContext.begin(provider="anthropic")
    ctx2 = RequestContext.get()
    
    assert ctx2.provider == "anthropic"


def test_tool_call_audit_creation():
    """Test ToolCallAudit dataclass."""
    audit = ToolCallAudit(
        call_id="test",
        tool_name="my_tool",
        arguments={"a": 1},
        result={"b": 2},
        duration_ms=50.0,
        error=None
    )
    
    assert audit.call_id == "test"
    assert audit.tool_name == "my_tool"
    assert audit.timestamp is not None


def test_tool_call_audit_with_error():
    """Test ToolCallAudit with error."""
    audit = ToolCallAudit(
        call_id="test",
        tool_name="failing_tool",
        arguments={},
        result=None,
        duration_ms=10.0,
        error="Tool execution failed"
    )
    
    assert audit.error == "Tool execution failed"
