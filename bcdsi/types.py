from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
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


from enum import IntEnum, Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional

class InterventionLevel(IntEnum):
    ALLOW = 1
    WARNING = 2
    MODIFY = 3
    BLOCK = 4
    MONITOR = 5  # ✅ 추가 (기존 값 유지)

# ...기존 PolicyType/SystemCriticality/InterventionRecord 정의는 그대로...


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
