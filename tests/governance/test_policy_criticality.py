"""PolicyResolver / CriticalityAssessor 계약 테스트.

threshold.py에서 분리된 두 모듈이 이전 동작을 그대로 유지하는지,
그리고 DynamicThreshold가 주입된 구현을 실제로 사용하는지 고정한다.
"""
import math

import pytest

from bcdsi import CriticalityAssessor, PolicyResolver
from bcdsi.threshold import DynamicThreshold, calculate_theta_integrity
from bcdsi.types import PolicyType as P
from bcdsi.types import SystemCriticality as C


@pytest.mark.parametrize("policy,expected", [
    (P.AGGRESSIVE, 0.05), (P.MODERATE, 0.1), (P.CONSERVATIVE, 0.15),
    (P.BALANCED, 0.2), (P.STRICT, 0.2), (P.LENIENT, 0.2),
])
def test_base_threshold_table(policy, expected):
    assert PolicyResolver().base_threshold(policy) == expected


@pytest.mark.parametrize("context,expected", [
    (None, P.BALANCED),
    ({}, P.BALANCED),
    ({"policy": P.STRICT}, P.STRICT),
    ({"policy": "aggressive"}, P.AGGRESSIVE),
    ({"policy": " Lenient "}, P.LENIENT),
    ({"policy": "unknown"}, P.BALANCED),
    ({"policy": 3}, P.BALANCED),
    ({"critical_system": True}, P.BALANCED),  # 플래그로 정책을 추측하지 않음
])
def test_resolve_explicit_only(context, expected):
    assert PolicyResolver().resolve(context) is expected


def test_resolve_custom_default():
    assert PolicyResolver(default=P.CONSERVATIVE).resolve({}) is P.CONSERVATIVE


@pytest.mark.parametrize("metrics,expected", [
    ({}, C.HIGH),
    (None, C.HIGH),
    ({"error_rate": float("nan"), "latency": None, "resource_usage": True}, C.HIGH),
    ({"error_rate": 0.2}, C.HIGH),
    ({"error_rate": 0.01}, C.MEDIUM),
    ({"error_rate": 0.01, "latency": 10, "resource_usage": 0.1}, C.LOW),
    ({"error_rate": 0.1, "latency": 10, "resource_usage": 0.1}, C.MEDIUM),
])
def test_assess_fail_closed(metrics, expected):
    assert CriticalityAssessor().assess(metrics) is expected


def test_assessor_thresholds_injectable():
    strict = CriticalityAssessor(high_error_rate=0.05)
    m = {"error_rate": 0.06, "latency": 10, "resource_usage": 0.1}
    assert CriticalityAssessor().assess(m) is C.LOW
    assert strict.assess(m) is C.HIGH
    assert DynamicThreshold(criticality_assessor=strict).get_system_criticality(m) is C.HIGH


def test_dynamic_threshold_uses_injected_resolver():
    r = PolicyResolver(base_thresholds={P.STRICT: 0.33}, theta_offsets={P.STRICT: 0.5})
    t = DynamicThreshold(policy_resolver=r)
    t.set_policy(P.STRICT)
    assert t.base_threshold == 0.33
    assert math.isclose(t.calculate_theta_integrity(0.0), 1.5)


def test_module_theta_matches_previous_formula():
    # 이전 구현: 1/(1+e) + policy_offset + criticality_offset
    got = calculate_theta_integrity(1.0, policy=P.AGGRESSIVE, system_criticality=C.HIGH)
    assert math.isclose(got, 0.5 - 0.07 - 0.02)
    got = calculate_theta_integrity(1.0, policy=P.CONSERVATIVE, system_criticality=C.LOW)
    assert math.isclose(got, 0.5 + 0.05 + 0.02)
