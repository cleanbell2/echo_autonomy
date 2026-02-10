# sicl/state_machine.py (실행 가능 v2.1)
from __future__ import annotations
from uuid import uuid4
import random
from .types import SICLState, DeltaLog, Task
from .world_sensor import WorldSensor
from .planner import Planner
from .gateway import GatewayNavigator
from .executor import Executor
from .ledger import AuditLedger
from .metrics import AutonomyMetrics


class DeltaLogCalculator:
    def compute(self, world_state) -> DeltaLog:
        obs = world_state.observations
        anomalies = []

        e_est = 0.1
        comp = 0.4

        fd = obs.get("force_dlog")
        if isinstance(fd, dict):
            if "e_est" in fd:
                e_est = float(fd["e_est"])
            if "comp" in fd:
                comp = float(fd["comp"])
            if "anomalies" in fd and isinstance(fd["anomalies"], list):
                anomalies.extend([str(x) for x in fd["anomalies"]])

        fm = obs.get("force_mode")
        if fm == "FREEZE":
            e_est = max(e_est, 0.85)
            comp = max(comp, 0.85)
        elif fm == "RESTRICTED":
            e_est = max(e_est, 0.55)
            comp = max(comp, 0.75)

        if any("<read_error" in str(v) for v in obs.values()):
            anomalies.append("read_error")
            e_est = max(e_est, 0.2)
            comp = max(comp, 0.6)

        return DeltaLog(comp=comp, e_est=e_est, anomalies=anomalies)


class SICLStateMachine:
    def __init__(
        self,
        sensor: WorldSensor,
        dlog_calc: DeltaLogCalculator,
        planner: Planner,
        gate: GatewayNavigator,
        executor: Executor,
        ledger: AuditLedger,
    ):
        self.sensor = sensor
        self.dlog_calc = dlog_calc
        self.planner = planner
        self.gate = gate
        self.executor = executor
        self.ledger = ledger

        self.metrics = AutonomyMetrics()
        self.state = SICLState.IDLE
        self.t = 0
        self.last_dlog: DeltaLog | None = None

    def tick(self, human_approved: bool = False, audit_prob: float = 0.05) -> None:
        trace_id = str(uuid4())

        # OBSERVE
        self.state = SICLState.OBSERVE
        world_state = self.sensor.read(self.t)

        # Planner에 user_input 전달
        world_state.observations["user_input"] = world_state.user_input

        # ASSESS
        self.state = SICLState.ASSESS
        dlog = self.dlog_calc.compute(world_state)
        self.last_dlog = dlog

        mode = self.gate.decide_mode(dlog)
        self.metrics.record_tick(mode)

        # PLAN
        self.state = SICLState.PLAN
        stasis_break = self.metrics.ticks >= 8 and self.metrics.S_stasis >= 0.7

        enriched_obs = world_state.observations.copy()
        enriched_obs["_current_s_stasis"] = self.metrics.S_stasis

        tasks = self.planner.propose(dlog, enriched_obs, stasis_break=stasis_break)

        # GATE
        self.state = SICLState.GATE
        chosen: tuple[Task, object] | None = None
        chosen_dec = None

        for cand in tasks:
            dec = self.gate.gate(dlog, cand, human_approved)
            if dec.action in ("ALLOW", "RESTRICT_ALLOW"):
                chosen = (cand, dec)
                chosen_dec = dec
                break

        # Ledger Pre-Commit
        self.ledger.append(
            "pre_commit",
            {
                "t": self.t,
                "mode": mode,
                "dlog": {"comp": dlog.comp, "e_est": dlog.e_est, "anomalies": dlog.anomalies},
                "chosen": (chosen[0].__dict__ if chosen else None),
                "decision": (chosen_dec.__dict__ if chosen_dec else None),
            },
            trace_id,
        )

        # ACT & REVIEW
        if chosen:
            task = chosen[0]
            self.state = SICLState.ACT
            res = self.executor.execute(task)

            self.metrics.record_action_weighted(task.type, task.payload, res.state_change_bits)

            # theta_drift_deg를 DeltaLog에 반영
            if "theta_drift_deg" in res.metrics:
                dlog.theta_drift_deg = res.metrics["theta_drift_deg"]

            # ← 벨님 제안: feedback_loop 호출
            if task.type == "REPLY_USER":
                self.planner.ego.feedback_loop(
                    dlog=dlog,
                    response_ok=res.ok,
                    user_reaction=None  # TODO: 다음 입력에서 감지
                )

            # Stasis-Break 학습
            if stasis_break and res.ok and res.state_change_bits > 0:
                self.planner.record_successful_break(task.type)

            self.state = SICLState.REVIEW
            if random.random() < audit_prob:
                self.ledger.append("sys_audit", {"trigger": "random", "prob": audit_prob}, trace_id)

            self.ledger.append(
                "post_receipt",
                {
                    "ok": res.ok,
                    "bits": res.state_change_bits,
                    "artifact": res.artifact,
                    "error": res.error,
                },
                trace_id,
            )
        else:
            self.ledger.append("post_receipt", {"skipped": True}, trace_id)

        # UPDATE
        self.state = SICLState.UPDATE
        self.metrics.record_closed_loop()
        self.t += 1
