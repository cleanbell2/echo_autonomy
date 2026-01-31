# tests/protocol/test_schemas.py
from __future__ import annotations

import pytest
from pydantic import ValidationError

from echo_gateway.protocol.schemas import (
    MessageRequest,
    ToolCallRequest,
    StatusRequest,
    MessageResponse,
    parse_request,
)


def test_message_request_ok_defaults():
    req = MessageRequest(content="hello")
    assert req.type == "message"
    assert req.metadata == {}


def test_message_request_reject_empty_content():
    with pytest.raises(ValidationError):
        MessageRequest(content="")


def test_message_request_reject_extra_field():
    with pytest.raises(ValidationError):
        MessageRequest(content="hi", extra_field=123)  # type: ignore


def test_tool_call_request_ok_defaults():
    req = ToolCallRequest(tool_name="calc", arguments={"x": 1})
    assert req.type == "tool_call"
    assert req.metadata == {}
    assert req.arguments["x"] == 1


def test_tool_call_request_reject_empty_tool_name():
    with pytest.raises(ValidationError):
        ToolCallRequest(tool_name="", arguments={})


def test_status_request_ok():
    req = StatusRequest(status="ping")
    assert req.type == "status"
    assert req.status == "ping"


def test_status_request_reject_invalid_status():
    with pytest.raises(ValidationError):
        StatusRequest(status="nope")  # type: ignore


def test_parse_request_message():
    r = parse_request({"type": "message", "content": "hi", "metadata": {"a": 1}})
    assert isinstance(r, MessageRequest)
    assert r.content == "hi"


def test_parse_request_tool_call():
    r = parse_request({"type": "tool_call", "tool_name": "t", "arguments": {"k": "v"}})
    assert isinstance(r, ToolCallRequest)
    assert r.tool_name == "t"


def test_parse_request_unknown_type():
    with pytest.raises(ValueError):
        parse_request({"type": "wat", "x": 1})  # type: ignore


def test_message_response_success_ok():
    res = MessageResponse(status="success", data={"ok": True})
    assert res.error is None


def test_message_response_error_requires_error_text():
    with pytest.raises(ValidationError):
        MessageResponse(status="error", data={"ok": False})  # error 누락


def test_message_response_non_error_forbids_error_field():
    with pytest.raises(ValidationError):
        MessageResponse(status="success", data={"ok": True}, error="should_not")  # error 금지


def test_message_response_pending_ok():
    res = MessageResponse(status="pending", data={"progress": 0.2})
    assert res.status == "pending"
    assert res.error is None
