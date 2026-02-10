from __future__ import annotations
import time
import hashlib
from typing import List
from .types import Task, DeltaLog
from .persona import EchoEgo

def _family_key(objective: str, window_sec: int = 60) -> str:
    bucket = int(time.time() // window_sec)
    raw = f"{objective}|{bucket}"
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"fam_{h}"

class Planner:
    def __init__(self):
        self._stasis_cooldown_until = 0.0
        self._dynamic_cooldown = 300.0
        self._last_successful_break = None
        self.ego = EchoEgo()

    def set_runtime_controls(self, stasis_cooldown_sec: float):
        self._dynamic_cooldown = stasis_cooldown_sec

    def propose(self, dlog: DeltaLog, world_obs: dict, stasis_break: bool = False) -> List[Task]:
        tasks: List[Task] = []

        # 0순위: 사용자 대화 (최우선)
        user_in = world_obs.get("user_input")
        if user_in:
            decision = self.ego.decide_intention(user_in)
            fam = _family_key("reply")

            tasks.append(
                Task(
                    task_id=f"{fam}.reply",
                    type="REPLY_USER",
                    e_est=0.1,
                    payload={"input": user_in, "decision": decision},
                    expected_effect_bits_min=1,
                )
            )

        # 1순위: 기존 루틴
        fam = _family_key("routine")
        tasks.append(
            Task(
                task_id=f"{fam}.report",
                type="WRITE_REPORT",
                e_est=min(0.35, max(0.15, dlog.e_est)),
                payload={"summary": "State Analysis", "comp": dlog.comp},
                expected_effect_bits_min=1,
            )
        )
        tasks.append(
            Task(
                task_id=f"{fam}.log",
                type="WRITE_LOG",
                e_est=min(0.10, dlog.e_est),
                payload={"msg": "Heartbeat", "tau_info": "in_ledger"},
                expected_effect_bits_min=1,
            )
        )
        tasks.append(
            Task(
                task_id=f"{fam}.sim",
                type="SIMULATE",
                e_est=min(0.05, dlog.e_est),
                payload={"what": "next_tick_plan"},
                expected_effect_bits_min=0,
            )
        )

        # Stasis Break
        now = time.time()
        if stasis_break and now >= self._stasis_cooldown_until:
            s_stasis = world_obs.get("_current_s_stasis", 0.7)

            if s_stasis > 0.9:
                action = "WRITE_REPORT"
            elif s_stasis > 0.7:
                action = "WRITE_LOG"
            else:
                action = "SIMULATE"

            if self._last_successful_break:
                action = self._last_successful_break

            tasks.insert(
                0,
                Task(
                    task_id=f"{fam}.break.{action.lower()}",
                    type=action,
                    e_est=0.08,
                    payload={"reason": "stasis_break", "level": s_stasis},
                    expected_effect_bits_min=1,
                ),
            )
            self._stasis_cooldown_until = now + self._dynamic_cooldown

        return tasks

    def record_successful_break(self, task_type: str):
        self._last_successful_break = task_type

