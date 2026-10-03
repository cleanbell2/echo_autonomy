from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import time


class PolicyType(Enum):
    STRICT = auto()
    MODERATE = auto()
    LENIENT = auto()
    BALANCED = auto()
    AGGRESSIVE = auto()
    CONSERVATIVE = auto()


class InterventionLevel(IntEnum):
    """값이 곧 심각도 순서. max()/비교로 합성 가능해야 하므로 번호를 바꿀 때 순서 유지 필수.

    이전 버전은 MONITOR=5 > BLOCK=4 로 순서가 역전되어 있었음.
    MONITOR는 intervene()에서 'θ 충분 + e 경고' (BCDSI 없음, 관찰 지속) 이므로 WARNING보다 낮음.
    """
    ALLOW = 1
    MONITOR = 2
    WARNING = 3
    MODIFY = 4
    BLOCK = 5


class SystemCriticality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class InterventionRecord:
    e_break_value: float
    theta_integrity: float
    threshold: float
    intervention_level: InterventionLevel
    action_taken: str
    effectiveness_score: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Optional[Dict[str, Any]] = None
    reason: str = ""


@dataclass
class EBreakMetrics:
    e_break_value: float
    timestamp: float = field(default_factory=lambda: time.time())
    vn_entropy: float = 0.0
    coherence: float = 0.0
    non_unitarity: float = 0.0
    metadata: dict = field(default_factory=dict)
