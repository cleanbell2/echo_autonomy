from __future__ import annotations
import time, hashlib, random
from typing import List
from .types import Task, DeltaLog, TaskType

def _family_key(objective: str, window_sec: int = 60) -> str:
    bucket = int(time.time() // window_sec)
    raw = f"{objective}|{bucket}"
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"fam_{h}"

class Planner:
    def __init__(self):
        self._stasis_cooldown_until = 0.0
        self._dynamic_cooldown = 300.0 # TauController가 주입

    def set_runtime_controls(self, stasis_cooldown_sec: float):
        self._dynamic_cooldown = stasis_cooldown_sec

    def propose(self, dlog: DeltaLog, world_obs: dict, stasis_break: bool = False) -> List[Task]:
        objective = "daily_snapshot" if not dlog.anomalies else "stability_check"
        fam = _family_key(objective)

        # 우선순위 큐 (거절 시 Fallback)
        tasks: List[Task] = [
            Task(task_id=f"{fam}.report", type="WRITE_REPORT", e_est=min(0.35, max(0.15, dlog.e_est)),
                 payload={"summary": "State Analysis", "comp": dlog.comp}, expected_effect_bits_min=1),
            Task(task_id=f"{fam}.log", type="WRITE_LOG", e_est=min(0.10, dlog.e_est),
                 payload={"msg": "Heartbeat", "tau_info": "in_ledger"}, expected_effect_bits_min=1),
            Task(task_id=f"{fam}.sim", type="SIMULATE", e_est=min(0.05, dlog.e_est),
                 payload={"what": "next_tick_plan"}, expected_effect_bits_min=0),
        ]

        # Stasis Break (TauController 쿨다운 적용)
        now = time.time()
        if stasis_break and now >= self._stasis_cooldown_until:
            safe = random.choice(["WRITE_LOG", "SIMULATE"])
            tasks.insert(0, Task(
                task_id=f"{fam}.break.{safe.lower()}", type=safe, e_est=0.08,
                payload={"reason": "stasis_break", "mode_hint": "SAFE"},
                expected_effect_bits_min=1
            ))
            self._stasis_cooldown_until = now + self._dynamic_cooldown

        return tasks
