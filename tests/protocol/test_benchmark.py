from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import pytest

from echo_gateway.protocol.envelope import Envelope
from echo_gateway.protocol.schemas import MessageRequest, parse_request
from echo_gateway.protocol.validator import sanitize_payload


def _now_ts() -> float:
    return datetime.now(tz=timezone.utc).timestamp()


@pytest.mark.skipif(
    os.environ.get("RUN_PROTOCOL_BENCH", "0") != "1",
    reason="set RUN_PROTOCOL_BENCH=1 to run performance benchmarks",
)
def test_protocol_validation_benchmark_smoke():
    """
    CI에서 흔들리지 않게 '기본은 스킵'으로 두고,
    필요할 때만 켜서 성능 회귀를 잡는다.

    목표(가이드):
    - 5,000회 파이프라인이 2.0초 이내면 충분히 빠른 편(환경 변동 고려)
    """
    N = 5000

    start = time.perf_counter()
    for _ in range(N):
        env = Envelope(
            session_id="sess-123",
            timestamp=_now_ts(),
            payload={"type": "message", "content": "hello"},
        )
        assert env.validate() is True
        payload = sanitize_payload(env.payload)
        req = parse_request(payload)
        assert isinstance(req, MessageRequest)
        _ = req.model_dump()
    elapsed = time.perf_counter() - start

    # 환경마다 편차가 있으니 과도하게 빡세게 잡지 않는다.
    assert elapsed < 2.0
