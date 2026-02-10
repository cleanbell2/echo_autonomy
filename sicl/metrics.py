from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import hashlib

@dataclass
class AutonomyMetrics:
    ticks: int = 0
    closed_loops: int = 0
    freezes: int = 0; restricts: int = 0
    weighted_actions: float = 0.0
    _recent_hashes: deque = field(default_factory=lambda: deque(maxlen=50))

    def record_tick(self, mode: str):
        self.ticks += 1
        if mode == "FREEZE": self.freezes += 1
        elif mode == "RESTRICTED": self.restricts += 1

    def record_action_weighted(self, t_type: str, payload: dict, bits: int):
        if bits <= 0: return
        h = hashlib.sha1(f"{t_type}|{payload}".encode()).hexdigest()
        novelty = 0.3 if h in self._recent_hashes else 1.0
        self._recent_hashes.append(h)
        
        impact = 1.0 if t_type == "WRITE_REPORT" else 0.4 if t_type == "WRITE_LOG" else 0.1
        self.weighted_actions += novelty * impact

    def record_closed_loop(self): self.closed_loops += 1

    @property
    def A_gain(self) -> float: return (self.weighted_actions / self.ticks) if self.ticks else 0.0
    @property
    def CL_rate(self) -> float: return (self.closed_loops / self.ticks) if self.ticks else 0.0
    @property
    def S_stasis(self) -> float: return ((self.freezes + self.restricts) / self.ticks) if self.ticks else 0.0
