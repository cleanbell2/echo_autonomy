"""
bcdsi 회귀 테스트 — 2026-10-02 실측으로 확인된 결함 7건.

1~4, 7: 수정 완료 → 일반 테스트
5     : D4 로 해결 (xfail 해제)
6     : 정책 엄격도 순서 미확정 → xfail(strict=True)
        결정 후 코드를 고치면 XPASS가 되어 테스트가 실패하므로, 그때 xfail 표시를 제거할 것.
"""
import math

import pytest

from bcdsi import calculate_theta_integrity as public_theta
from bcdsi.intervention import (
    BCDSIInterventionHistory,
    format_intervention_message,
    intervene,
)
from bcdsi.threshold import DynamicThreshold, create_policy_based_threshold
from bcdsi.types import InterventionLevel as L
from bcdsi.types import PolicyType as P
from bcdsi.types import SystemCriticality as C


# ---------- 1. timestamp 타입 불일치 → format_intervention_message 크래시 ----------
def test_format_message_does_not_crash_on_real_record():
    msg = format_intervention_message(intervene(0.1, 0.9, 0.5))
    assert "INTERVENTION" in msg and "N/A" not in msg


def test_format_message_accepts_legacy_float_timestamp():
    rec = intervene(0.1, 0.9, 0.5)
    rec.timestamp = 1785640790.0           # 이전 버전이 만든 레코드 호환
    assert "INTERVENTION" in format_intervention_message(rec)


# ---------- 2. 심각도 순서 역전 (MONITOR=5 > BLOCK=4) ----------
def test_severity_order_total():
    assert L.ALLOW < L.MONITOR < L.WARNING < L.MODIFY < L.BLOCK
    assert max(L.BLOCK, L.MONITOR) is L.BLOCK


def test_riskier_input_never_gets_lower_level():
    near = intervene(0.5, 0.09, 0.1)        # θ가 임계 근처 → WARNING
    safe = intervene(0.5, 0.15, 0.1)        # θ 충분 → MONITOR
    assert near.intervention_level > safe.intervention_level


# ---------- 3. 히스토리 카운트 드리프트 (MONITOR 추가/제거 키 불일치) ----------
def test_history_counts_never_negative_and_match_records():
    h = BCDSIInterventionHistory(max_history=3)
    for _ in range(6):
        h.add_record(intervene(0.5, 0.15, 0.1))           # MONITOR 6건
    for args in [(2.0, 0.05, 0.1), (1.0, 0.08, 0.1)]:     # BLOCK, MODIFY
        h.add_record(intervene(*args))
    assert all(v >= 0 for v in h.intervention_counts.values())
    assert sum(h.intervention_counts.values()) == len(h.records) == 3


# ---------- 4. fail-open: 메트릭 누락 → LOW ----------
@pytest.mark.parametrize("metrics", [
    {},
    {"error_rate": None, "latency": None, "resource_usage": None},
    {"error_rate": math.nan, "latency": 10.0, "resource_usage": 0.3},
])
def test_criticality_unknown_is_not_low(metrics):
    assert DynamicThreshold().get_system_criticality(metrics) is not C.LOW


def test_criticality_all_missing_is_high():
    assert DynamicThreshold().get_system_criticality({}) is C.HIGH


def test_criticality_partial_cannot_certify_low():
    # 측정된 값이 전부 양호해도, 빠진 항목이 있으면 LOW라고 단정할 수 없음
    assert DynamicThreshold().get_system_criticality({"error_rate": 0.01}) is C.MEDIUM


def test_criticality_known_values_unchanged():
    t = DynamicThreshold()
    assert t.get_system_criticality(
        {"error_rate": 0.05, "latency": 10.0, "resource_usage": 0.3}) is C.LOW
    assert t.get_system_criticality(
        {"error_rate": 0.2, "latency": 80.0, "resource_usage": 0.9}) is C.HIGH
    assert t.get_system_criticality(
        {"error_rate": 0.1, "latency": 40.0, "resource_usage": 0.6}) is C.MEDIUM


# ---------- 7. update()가 생성자 base_threshold를 덮어씀 ----------
def test_update_keeps_constructor_base_threshold():
    t = create_policy_based_threshold(base_threshold=0.85, policy=P.BALANCED)
    t.update(0.0)
    assert t.base_threshold == 0.85


def test_set_policy_still_overrides_base():
    t = DynamicThreshold(base_threshold=0.85)
    t.set_policy(P.CONSERVATIVE)
    t.update(0.0)
    assert t.base_threshold == 0.15


# ---------- 5. 같은 이름 θ 함수 2개가 다른 값 → D4 로 해결 ----------
# D4 해결 (PR #12, 2026-10-03 Bell 승인): 메서드가 모듈 함수로 위임
def test_theta_single_source_of_truth():
    kw = dict(e_break_value=0.2, history=[0.9, 0.5])
    a = DynamicThreshold(policy=P.BALANCED).calculate_theta_integrity(**kw)
    b = public_theta(policy=P.BALANCED, **kw)
    assert a == pytest.approx(b)


# ---------- 6. LENIENT == STRICT == BALANCED == 0.2 (결정 필요) ----------
def _base(p):
    t = DynamicThreshold()
    t.set_policy(p)
    return t.base_threshold


@pytest.mark.xfail(strict=True, reason=(
    "LENIENT/BALANCED의 base_threshold 값 결정 필요. 현재 셋 다 0.2(가장 엄격). "
    "BALANCED는 create_policy_based_threshold 기본값이라 바꾸면 기본 개입 빈도가 변함"))
def test_policy_strictness_is_monotonic():
    assert _base(P.AGGRESSIVE) <= _base(P.LENIENT) < _base(P.STRICT)
    assert _base(P.MODERATE) <= _base(P.BALANCED) < _base(P.STRICT)


def test_theta_method_ignores_component_terms_no_double_counting():
    t = DynamicThreshold(policy=P.BALANCED)
    a = t.calculate_theta_integrity(1.0)
    b = t.calculate_theta_integrity(1.0, vn_entropy=0.5, coherence=0.3, non_unitarity=0.2)
    assert a == b == pytest.approx(0.5)


def test_theta_canonical_bounds_and_fail_closed():
    assert public_theta(0.0, policy=P.CONSERVATIVE) == 1.0          # 1.05 → 상한 1
    assert public_theta(float("nan")) == 0.0
    assert public_theta(float("inf")) == 0.0
    xs = [0.0, 0.5, 1.0, 2.0, 5.0]
    th = [public_theta(x) for x in xs]
    assert th == sorted(th, reverse=True)
