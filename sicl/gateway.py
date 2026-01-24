from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Set
import time
from .types import DeltaLog, Task, GateDecision, Mode

@dataclass
class _EEvent:
    ts: float; e: float

ALLOWED_BY_MODE = {
    "NORMAL": {"READ_ONLY_QUERY","WRITE_LOG","WRITE_REPORT","SIMULATE"},
    "RESTRICTED": {"READ_ONLY_QUERY","WRITE_LOG","WRITE_REPORT","SIMULATE"},
    "FREEZE": {"READ_ONLY_QUERY","WRITE_LOG"},
}
HIGH_RISK = {"SYSTEM_CHANGE","NETWORK_POST","TRADE"}

class GatewayNavigator:
    def __init__(self, split_window_sec: int = 120, split_cum_threshold: float = 0.70):
        self.split_window_sec = split_window_sec
        self.split_cum_threshold = split_cum_threshold
        self._family_events: Dict[str, Deque[_EEvent]] = defaultdict(deque)

    def _family_id(self, task_id: str) -> str:
        return task_id.split(".")[0]

    def gate(self, dlog: DeltaLog, task: Task, human_approved: bool = False) -> GateDecision:
        # 모드 결정
        mode: Mode = "NORMAL"
        if dlog.e_est >= 0.8: mode = "FREEZE"
        elif dlog.e_est >= 0.5 or dlog.comp >= 0.75: mode = "RESTRICTED"

        # 분할 실행 회피 탐지 (Sliding Window)
        fam = self._family_id(task.task_id)
        now = time.time()
        q = self._family_events[fam]
        while q and (now - q[0].ts) > self.split_window_sec: q.popleft()
        
        q.append(_EEvent(now, task.e_est))
        if sum(ev.e for ev in q) > self.split_cum_threshold:
            return GateDecision("RESTRICT_ALLOW", "RESTRICTED", "split_detect_limit_exceeded")

        # 기본 허용 목록 체크
        allowed = ALLOWED_BY_MODE[mode]
        if task.type not in allowed:
            if mode == "FREEZE": return GateDecision("FREEZE", mode, "blocked_in_freeze")
            if task.type in HIGH_RISK: return GateDecision("REQUIRE_APPROVAL", mode, "high_risk")
            return GateDecision("DENY", mode, "not_allowed")

        return GateDecision(("ALLOW" if mode=="NORMAL" else "RESTRICT_ALLOW"), mode, "ok")
