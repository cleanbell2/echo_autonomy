"""CriticalityAssessor: 시스템 메트릭 → SystemCriticality.

DynamicThreshold.get_system_criticality()에 있던 fail-closed 판정을 분리했다.
판정 규칙과 경계값은 이전 구현과 동일하다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .types import SystemCriticality

# θ_integrity 계산 시 중요도별 가산 보정.
CRITICALITY_THETA_OFFSET: Dict[SystemCriticality, float] = {
    SystemCriticality.HIGH: -0.02,
    SystemCriticality.LOW: 0.02,
}


@dataclass(frozen=True)
class CriticalityAssessor:
    """Fail-closed: 측정 불가(누락/None/NaN/bool)를 '정상'으로 간주하지 않는다.

    - 측정값 중 하나라도 HIGH 조건 → HIGH
    - 세 항목 모두 측정 불가 → HIGH
    - 일부만 측정됨 → LOW 단정 불가, 최소 MEDIUM
    """

    high_error_rate: float = 0.15
    high_latency: float = 60.0
    high_resource_usage: float = 0.8
    low_error_rate: float = 0.08
    low_latency: float = 30.0
    low_resource_usage: float = 0.5

    KEYS = ("error_rate", "latency", "resource_usage")

    @classmethod
    def _measured(cls, metrics: Optional[Mapping[str, Any]]) -> Dict[str, float]:
        vals: Dict[str, float] = {}
        for k in cls.KEYS:
            v = (metrics or {}).get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
                vals[k] = float(v)
        return vals

    def assess(self, metrics: Optional[Mapping[str, Any]]) -> SystemCriticality:
        vals = self._measured(metrics)
        if not vals:
            return SystemCriticality.HIGH
        if (vals.get("error_rate", 0.0) > self.high_error_rate
                or vals.get("latency", 0.0) > self.high_latency
                or vals.get("resource_usage", 0.0) > self.high_resource_usage):
            return SystemCriticality.HIGH
        if (len(vals) == len(self.KEYS)
                and vals["error_rate"] < self.low_error_rate
                and vals["latency"] < self.low_latency
                and vals["resource_usage"] < self.low_resource_usage):
            return SystemCriticality.LOW
        return SystemCriticality.MEDIUM

    @staticmethod
    def theta_offset(criticality: SystemCriticality) -> float:
        return CRITICALITY_THETA_OFFSET.get(criticality, 0.0)
