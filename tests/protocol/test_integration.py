from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from echo_gateway.protocol.envelope import Envelope
from echo_gateway.protocol.schemas import (
    MessageRequest,
    ToolCallRequest,
    StatusRequest,
    MessageResponse,
    parse_request,
)
from echo_gateway.protocol.validator import (
    sanitize_session_id,
    sanitize_payload,
    ensure_json_serializable,
    validate_size,
)


def _now_ts() -> float:
    return datetime.now(tz=timezone.utc).timestamp()


def test_full_request_pipeline_message_ok():
    # 1) session_id sanitize
    sid = sanitize_session_id("sess/../ok??")
    assert sid

    # 2) envelope 생성
    env = Envelope(
        session_id=sid,
        timestamp=_now_ts(),
        payload={"type": "message", "content": "hello", "metadata": {"user": "alice"}},
    )

    # 3) envelope validate (recency 등)
    env.validate()  # Raises ValueError if invalid

    # 4) payload sanitize + json safety + depth protection
    payload = sanitize_payload(env.payload)
    ensure_json_serializable(payload)

    # 5) schema parse
    req = parse_request(payload)
    assert isinstance(req, MessageRequest)
    assert req.content == "hello"
    assert req.metadata["user"] == "alice"


def test_full_request_pipeline_tool_call_ok():
    env = Envelope(
        session_id=sanitize_session_id("sess-123"),
        timestamp=_now_ts(),
        payload={"type": "tool_call", "tool_name": "calculator", "arguments": {"x": 1}},
    )
    env.validate()  # Raises ValueError if invalid
    payload = sanitize_payload(env.payload)
    req = parse_request(payload)
    assert isinstance(req, ToolCallRequest)
    assert req.tool_name == "calculator"
    assert req.arguments["x"] == 1


def test_full_request_pipeline_status_ok():
    env = Envelope(
        session_id="sess-123",
        timestamp=_now_ts(),
        payload={"type": "status", "status": "ping"},
    )
    env.validate()  # Raises ValueError if invalid
    payload = sanitize_payload(env.payload)
    req = parse_request(payload)
    assert isinstance(req, StatusRequest)
    assert req.status == "ping"


def test_pipeline_rejects_unknown_request_type_fail_closed():
    env = Envelope(
        session_id="sess-123",
        timestamp=_now_ts(),
        payload={"type": "unknown", "x": 1},
    )
    env.validate()  # Raises ValueError if invalid
    payload = sanitize_payload(env.payload)
    with pytest.raises(ValueError):
        parse_request(payload)


def test_pipeline_rejects_extra_fields_pydantic_forbid():
    env = Envelope(
        session_id="sess-123",
        timestamp=_now_ts(),
        payload={"type": "message", "content": "hi", "extra_field": 123},
    )
    env.validate()  # Raises ValueError if invalid
    payload = sanitize_payload(env.payload)
    with pytest.raises(ValidationError):
        parse_request(payload)


def test_pipeline_rejects_nesting_bomb():
    deep = cur = {"type": "message", "content": "hi", "nest": {}}
    cur = deep["nest"]
    for _ in range(40):
        nxt = {}
        cur["x"] = nxt
        cur = nxt

    env = Envelope(session_id="sess-123", timestamp=_now_ts(), payload=deep)
    env.validate()  # Raises ValueError if invalid
    with pytest.raises(ValueError):
        sanitize_payload(env.payload, max_depth=32)


def test_pipeline_rejects_non_json_serializable():
    env = Envelope(
        session_id="sess-123",
        timestamp=_now_ts(),
        payload={"type": "message", "content": "hi", "metadata": {"f": lambda x: x}},
    )
    env.validate()  # Raises ValueError if invalid
    # sanitize_payload 내부에서 ensure_json_serializable을 호출하므로
    # sanitize_payload 자체가 ValueError를 발생시킨다
    with pytest.raises(ValueError):
        sanitize_payload(env.payload)


def test_pipeline_size_limit_smoke():
    raw = b"a" * (10 * 1024 * 1024)  # 10MB
    assert validate_size(raw, max_mb=10) is True
    assert validate_size(raw + b"x", max_mb=10) is False


def test_full_response_pipeline_success_ok():
    # 응답은 schema 규칙만으로도 충분히 fail-closed
    res = MessageResponse(status="success", data={"ok": True})
    dumped = res.model_dump()
    assert dumped["status"] == "success"
    assert "error" in dumped and dumped["error"] is None
