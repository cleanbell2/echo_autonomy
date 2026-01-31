# tests/protocol/test_validator.py
from __future__ import annotations

import pytest

from echo_gateway.protocol.validator import (
    validate_size,
    sanitize_session_id,
    ensure_json_serializable,
    sanitize_payload,
)


def test_validate_size_under_limit():
    assert validate_size(b"a" * 10, max_mb=1) is True


def test_validate_size_over_limit():
    assert validate_size(b"a" * (1024 * 1024 + 1), max_mb=1) is False


def test_validate_size_invalid_max_mb():
    assert validate_size(b"a", max_mb=0) is False
    assert validate_size(b"a", max_mb=-1) is False


def test_sanitize_session_id_basic():
    assert sanitize_session_id("sess-123") == "sess-123"
    assert sanitize_session_id("  sess-123  ") == "sess-123"


def test_sanitize_session_id_replaces_bad_chars():
    s = sanitize_session_id("sess/../evil??")
    assert "/" not in s and "?" not in s
    assert len(s) > 0


def test_sanitize_session_id_empty_after_sanitize_raises():
    with pytest.raises(ValueError):
        sanitize_session_id("   ")


def test_sanitize_session_id_max_len_truncates():
    long = "a" * 999
    s = sanitize_session_id(long, max_len=32)
    assert len(s) == 32


def test_ensure_json_serializable_ok():
    ensure_json_serializable({"a": 1, "b": [1, 2, 3]})


def test_ensure_json_serializable_rejects_function():
    with pytest.raises(ValueError):
        ensure_json_serializable({"bad": lambda x: x})  # type: ignore


def test_sanitize_payload_ok():
    out = sanitize_payload({"type": "message", "content": "hi"})
    assert out["type"] == "message"


def test_sanitize_payload_reject_non_dict():
    with pytest.raises(TypeError):
        sanitize_payload(["nope"])  # type: ignore


def test_sanitize_payload_reject_too_deep():
    x = cur = {}
    for _ in range(40):
        nxt = {}
        cur["x"] = nxt
        cur = nxt
    with pytest.raises(ValueError):
        sanitize_payload(x, max_depth=16)
