from __future__ import annotations

import math
from typing import Optional

from .criticality import CriticalityAssessor
from .policy import PolicyResolver
from .types import PolicyType, SystemCriticality

_DEFAULT_RESOLVER = PolicyResolver()
_DEFAULT_ASSESSOR = CriticalityAssessor()


class DynamicThreshold:
    """정책(PolicyResolver)과 중요도(CriticalityAssessor)를 주입받아 임계값을 조정한다.

    정책별 상수와 중요도 판정 규칙은 각 모듈이 소유하고, 여기서는 조립만 한다.
    """

    def __init__(self, base_threshold: float = 0.1, policy: PolicyType = PolicyType.CONSERVATIVE, min_threshold: float = 0.0, max_threshold: float = 1.0, adaptation_rate: float = 0.1,
                 *, policy_resolver: Optional[PolicyResolver] = None,
                 criticality_assessor: Optional[CriticalityAssessor] = None):
        self.policy_resolver = policy_resolver or _DEFAULT_RESOLVER
        self.criticality_assessor = criticality_assessor or _DEFAULT_ASSESSOR
        self.base_threshold = base_threshold
        self.policy = policy
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.adaptation_rate = adaptation_rate
        self.threshold_history = []
        self.current_threshold = self.base_threshold

    def set_policy(self, policy: PolicyType):
        self.policy = policy
        self.base_threshold = self.policy_resolver.base_threshold(policy)
        self.current_threshold = self.base_threshold

    def update(self, metric_value: float):
        # base_threshold는 생성자 또는 set_policy()가 결정. 여기서 정책으로 재계산하면
        # create_policy_based_threshold(base_threshold=...) 값이 첫 update에서 사라짐.
        # metric_value에 따라 threshold를 조정하는 로직(예시)
        new_threshold = self.base_threshold + (metric_value * 0.01)
        self._update_threshold(new_threshold)
        return self.current_threshold

    def _update_threshold(self, latest_integrity: float) -> None:
        def _clamp01(x):
            return max(0.0, min(1.0, x))
        integ = _clamp01(float(latest_integrity))
        # 낮은 integrity일수록 threshold를 강하게 내리는 target
        target = self.base_threshold * (0.6 + 0.5 * integ)
        new_thr = (1.0 - self.adaptation_rate) * self.current_threshold + self.adaptation_rate * target
        new_thr = max(self.min_threshold, min(new_thr, self.max_threshold))
        self.current_threshold = float(new_thr)
        self.threshold_history.append(self.current_threshold)

    def get_threshold_statistics(self):
        values = self.threshold_history[-20:] if self.threshold_history else [self.current_threshold]
        n = len(values)
        mean = sum(values) / n if n else 0.0
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n else 0.0
        return {
            "mean": mean,
            "std": std,
            "current": self.current_threshold,
            "history": self.threshold_history[-10:],
        }

    def calculate_theta_integrity(self, e_break_value: float, vn_entropy: float = 0.0, coherence: float = 0.0, non_unitarity: float = 0.0, history: list = None, historical_theta: list = None) -> float:
        e = float(e_break_value)
        base = 1.0 / (1.0 + max(0.0, e))
        base += self.policy_resolver.theta_offset(self.policy)
        hist = historical_theta if historical_theta is not None else history
        if hist and len(hist) > 1:
            slope = (hist[-1] - hist[0]) / max(1, len(hist) - 1)
            if slope < 0:
                base -= abs(slope) * 2
            else:
                base += 0.5 * slope
        base -= 0.1 * vn_entropy
        base -= 0.1 * coherence
        base -= 0.1 * non_unitarity
        return max(0.0, base)

    def get_system_criticality(self, metrics: dict) -> SystemCriticality:
        """Fail-closed 판정은 CriticalityAssessor가 소유한다."""
        return self.criticality_assessor.assess(metrics)


def create_policy_based_threshold(
    base_threshold: float = 0.85,
    policy: PolicyType = PolicyType.BALANCED,
    min_threshold: float = 0.0,
    max_threshold: float = 1.0,
    adaptation_rate: float = 0.1,
) -> DynamicThreshold:
    return DynamicThreshold(
        base_threshold=base_threshold,
        policy=policy,
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        adaptation_rate=adaptation_rate,
    )

def calculate_theta_integrity(
    e_break_value: float,
    policy: PolicyType = PolicyType.BALANCED,
    system_criticality: SystemCriticality = SystemCriticality.MEDIUM,
    min_theta: float = 0.0,
    history: list = None,
) -> float:
    e = float(e_break_value)
    base = 1.0 / (1.0 + max(0.0, e))
    base += _DEFAULT_RESOLVER.theta_offset(policy)
    base += CriticalityAssessor.theta_offset(system_criticality)
    if history and len(history) > 2:
        slope = (history[-1] - history[0]) / max(1, len(history) - 1)
        base += 0.5 * slope
    return max(min_theta, base)
