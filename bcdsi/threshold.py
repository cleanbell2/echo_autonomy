from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .types import PolicyType, SystemCriticality

class DynamicThreshold:
    def __init__(self, base_threshold: float = 0.1, policy: PolicyType = PolicyType.CONSERVATIVE, min_threshold: float = 0.0, max_threshold: float = 1.0, adaptation_rate: float = 0.1):
        self.base_threshold = base_threshold
        self.policy = policy
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.adaptation_rate = adaptation_rate
        self.threshold_history = []
        self.current_threshold = self.base_threshold

    def set_policy(self, policy: PolicyType):
        self.policy = policy
        if policy == PolicyType.AGGRESSIVE:
            self.base_threshold = 0.05
        elif policy == PolicyType.MODERATE:
            self.base_threshold = 0.1
        elif policy == PolicyType.CONSERVATIVE:
            self.base_threshold = 0.15
        else:
            self.base_threshold = 0.2
        self.current_threshold = self.base_threshold

    def update(self, metric_value: float):
        # 정책에 따라 base_threshold를 즉시 반영
        if self.policy == PolicyType.AGGRESSIVE:
            self.base_threshold = 0.05
        elif self.policy == PolicyType.MODERATE:
            self.base_threshold = 0.1
        elif self.policy == PolicyType.CONSERVATIVE:
            self.base_threshold = 0.15
        else:
            self.base_threshold = 0.2
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
        import math
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
        if self.policy == PolicyType.CONSERVATIVE:
            base += 0.05
        elif self.policy == PolicyType.AGGRESSIVE:
            base -= 0.07
        elif self.policy == PolicyType.LENIENT:
            base -= 0.03
        elif self.policy == PolicyType.STRICT:
            base -= 0.01
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
        from .types import SystemCriticality
        if metrics.get('error_rate', 0) > 0.15 or metrics.get('latency', 0) > 60 or metrics.get('resource_usage', 0) > 0.8:
            return SystemCriticality.HIGH
        elif metrics.get('error_rate', 0) < 0.08 and metrics.get('latency', 0) < 30 and metrics.get('resource_usage', 0) < 0.5:
            return SystemCriticality.LOW
        else:
            return SystemCriticality.MEDIUM

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
    if policy == PolicyType.CONSERVATIVE:
        base += 0.05
    elif policy == PolicyType.AGGRESSIVE:
        base -= 0.07
    elif policy == PolicyType.LENIENT:
        base -= 0.03
    elif policy == PolicyType.STRICT:
        base -= 0.01
    if system_criticality == SystemCriticality.HIGH:
        base -= 0.02
    elif system_criticality == SystemCriticality.LOW:
        base += 0.02
    if history and len(history) > 2:
        slope = (history[-1] - history[0]) / max(1, len(history) - 1)
        base += 0.5 * slope
    return max(min_theta, base)
