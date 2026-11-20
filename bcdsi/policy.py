"""PolicyResolver: 런타임 컨텍스트 → PolicyType, PolicyType → 정책 파라미터.

threshold.py 안에 if/elif로 흩어져 있던 정책별 상수를 한 곳에 고정한다.
값은 이전 구현과 동일하다 (test_bcdsi.py / tests/governance 가 스펙).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from .types import PolicyType

# set_policy()가 적용하는 base_threshold. 표에 없는 정책은 _DEFAULT_BASE_THRESHOLD.
POLICY_BASE_THRESHOLD: Dict[PolicyType, float] = {
    PolicyType.AGGRESSIVE: 0.05,
    PolicyType.MODERATE: 0.1,
    PolicyType.CONSERVATIVE: 0.15,
}
_DEFAULT_BASE_THRESHOLD = 0.2

# θ_integrity 계산 시 정책별 가산 보정. 표에 없는 정책은 0.
POLICY_THETA_OFFSET: Dict[PolicyType, float] = {
    PolicyType.CONSERVATIVE: 0.05,
    PolicyType.AGGRESSIVE: -0.07,
    PolicyType.LENIENT: -0.03,
    PolicyType.STRICT: -0.01,
}


@dataclass
class PolicyResolver:
    """정책 주입 지점.

    resolve()는 컨텍스트에 명시된 정책만 따른다 (context["policy"]: PolicyType 또는 이름).
    명시가 없거나 해석 불가하면 default로 떨어진다 — 컨텍스트 플래그로 정책을 추측하지 않음.
    """

    default: PolicyType = PolicyType.BALANCED
    base_thresholds: Mapping[PolicyType, float] = field(
        default_factory=lambda: dict(POLICY_BASE_THRESHOLD))
    theta_offsets: Mapping[PolicyType, float] = field(
        default_factory=lambda: dict(POLICY_THETA_OFFSET))

    def resolve(self, context: Optional[Mapping[str, Any]] = None) -> PolicyType:
        raw = (context or {}).get("policy")
        if isinstance(raw, PolicyType):
            return raw
        if isinstance(raw, str):
            try:
                return PolicyType[raw.strip().upper()]
            except KeyError:
                pass
        return self.default

    def base_threshold(self, policy: PolicyType) -> float:
        return self.base_thresholds.get(policy, _DEFAULT_BASE_THRESHOLD)

    def theta_offset(self, policy: PolicyType) -> float:
        return self.theta_offsets.get(policy, 0.0)
