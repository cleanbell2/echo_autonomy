# sicl/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Literal

Mode = Literal["NORMAL", "RESTRICTED", "FREEZE"]

TaskType = Literal[
    "READ_ONLY_QUERY",
    "WRITE_LOG",
    "WRITE_REPORT",
    "SIMULATE",
    "REPLY_USER",
    "SYSTEM_CHANGE",
    "NETWORK_POST",
    "TRADE",
]

class SICLState(Enum):
    IDLE = auto()
    OBSERVE = auto()
    ASSESS = auto()
    PLAN = auto()
    GATE = auto()
    ACT = auto()
    REVIEW = auto()
    UPDATE = auto()

@dataclass
class WorldState:
    t: int
    observations: Dict[str, Any] = field(default_factory=dict)
    user_input: Optional[str] = None

@dataclass
class DeltaLog:
    psi: float = 0.5
    phi: float = 0.5
    chi: float = 0.5
    omega: float = 0.5
    comp: float = 0.5
    e_est: float = 0.0
    theta_drift_deg: float = 0.0
    anomalies: List[str] = field(default_factory=list)

@dataclass
class Task:
    task_id: str
    type: TaskType
    requires_human: bool = False
    e_est: float = 0.0
    payload: Dict[str, Any] = field(default_factory=dict)
    expected_effect_bits_min: int = 1

@dataclass
class GateDecision:
    action: Literal["ALLOW", "RESTRICT_ALLOW", "REQUIRE_APPROVAL", "DENY", "FREEZE"]
    mode: Mode
    reason: str

@dataclass
class ActResult:
    ok: bool
    artifact: Optional[str] = None
    state_change_bits: int = 0
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
