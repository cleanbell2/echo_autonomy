"""
Test gateway pipeline — Phase 4
"""

import time

import pytest

from echo_gateway.executor.local import LocalExecutor
from echo_gateway.gateway.pipeline import SafetyDecision, handle_inbound


def stub_safety_allow(stage: str, payload):
    """Stub safety check — always ALLOW."""
    return SafetyDecision(level="ALLOW")


def stub_safety_block(stage: str, payload):
    """Stub safety check — always BLOCK."""
    return SafetyDecision(level="BLOCK", reason="test block")


@pytest.mark.asyncio
async def test_pipeline_message_happy_path():
    """Pipeline processes valid MessageRequest."""
    envelope = {
        "session_id": "test-session",
        "timestamp": time.time(),
        "payload": {
            "type": "message",
            "content": "Hello pipeline",
            "metadata": {},
        },
    }
    executor = LocalExecutor()
    result = await handle_inbound(envelope, executor, stub_safety_allow)
    assert result["status"] == "success"
    assert result["data"]["echo"] == "Hello pipeline"


@pytest.mark.asyncio
async def test_pipeline_tool_call():
    """Pipeline processes valid ToolCallRequest."""
    envelope = {
        "session_id": "tool-session",
        "timestamp": time.time(),
        "payload": {
            "type": "tool_call",
            "tool_name": "calculator",
            "arguments": {"op": "add"},
        },
    }
    executor = LocalExecutor()
    result = await handle_inbound(envelope, executor, stub_safety_allow)
    assert result["status"] == "success"
    assert result["data"]["tool_name"] == "calculator"


@pytest.mark.asyncio
async def test_pipeline_safety_block():
    """Pipeline blocks when safety check returns BLOCK."""
    envelope = {
        "session_id": "test-session",
        "timestamp": time.time(),
        "payload": {
            "type": "message",
            "content": "blocked content",
            "metadata": {},
        },
    }
    executor = LocalExecutor()
    result = await handle_inbound(envelope, executor, stub_safety_block)
    assert result["status"] == "error"
    assert "Blocked" in result["error"]


@pytest.mark.asyncio
async def test_pipeline_invalid_envelope():
    """Pipeline returns error for invalid envelope."""
    envelope = {
        "session_id": "bad-session",
        "timestamp": 0,  # too old
        "payload": {"type": "message", "content": "test"},
    }
    executor = LocalExecutor()
    result = await handle_inbound(envelope, executor, stub_safety_allow)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_pipeline_unknown_request_type():
    """Pipeline returns error for unknown request type."""
    envelope = {
        "session_id": "test-session",
        "timestamp": time.time(),
        "payload": {"type": "unknown_type"},
    }
    executor = LocalExecutor()
    result = await handle_inbound(envelope, executor, stub_safety_allow)
    assert result["status"] == "error"
