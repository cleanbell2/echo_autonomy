# echo_gateway/protocol/validator.py
from __future__ import annotations

import json
import re
from typing import Any, Dict


_SESSION_ID_RE = re.compile(r"[^a-zA-Z0-9_\-:.]+")


def validate_size(data: bytes, max_mb: int = 10) -> bool:
    """
    바이트 크기 제한.
    - 기본 10MB
    - max_mb가 0 이하이면 무조건 거부
    """
    if max_mb <= 0:
        return False
    limit = max_mb * 1024 * 1024
    return len(data) <= limit


def sanitize_session_id(session_id: str, *, max_len: int = 128) -> str:
    """
    위험 문자 제거 + 길이 제한.
    허용: 영숫자, _, -, :, ., (그리고 구분자용으로 :)
    """
    if not isinstance(session_id, str):
        raise TypeError("session_id must be str")

    s = session_id.strip()
    s = _SESSION_ID_RE.sub("_", s)

    # 연속 언더스코어 정리
    s = re.sub(r"_+", "_", s)

    if len(s) == 0:
        raise ValueError("session_id is empty after sanitization")

    if len(s) > max_len:
        s = s[:max_len]

    return s


def ensure_json_serializable(obj: Any) -> None:
    """
    payload/data가 JSON 직렬화 가능한지 확인.
    실패하면 ValueError.
    """
    try:
        json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception as e:
        raise ValueError("object is not JSON-serializable") from e


def sanitize_payload(payload: Dict[str, Any], *, max_depth: int = 32) -> Dict[str, Any]:
    """
    아주 보수적 "구조 안정성" 체크:
    - dict만 받음
    - JSON 직렬화 가능해야 함
    - 과도한 중첩을 간단히 차단(재귀 폭탄 방어)
    """
    if not isinstance(payload, dict):
        raise TypeError("payload must be dict")

    _check_depth(payload, max_depth=max_depth)
    ensure_json_serializable(payload)
    return payload


def _check_depth(x: Any, *, max_depth: int) -> None:
    if max_depth < 0:
        raise ValueError("payload nesting too deep")

    if isinstance(x, dict):
        for k, v in x.items():
            _check_depth(k, max_depth=max_depth - 1)
            _check_depth(v, max_depth=max_depth - 1)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _check_depth(v, max_depth=max_depth - 1)
    else:
        # primitive/기타는 depth만 소비
        return
