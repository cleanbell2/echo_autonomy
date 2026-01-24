from __future__ import annotations
from uuid import uuid4
import random
from .types import SICLState, DeltaLog
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
        if any("<read_error" in str(v) for v in obs.values()): anomalies.append("read_error")
        # 더미 로직 (나중에 v3.4 연결)
        e_est = 0.2 if anomalies else 0.1
        comp = 0.6 if anomalies else 0.4
        return DeltaLog(comp=comp, e_est=e_est, anomalies=anomalies)

class SICLStateMachine:
    def __init__(self, sensor, dlog_calc, planner, gate, executor, ledger):
        self.sensor = sensor; self.dlog_calc = dlog_calc
        self.planner = planner; self.gate = gate
        self.executor = executor; self.ledger = ledger
        self.metrics = AutonomyMetrics()
        self.state = SICLState.IDLE
        self.t = 0
        self.last_dlog = None

    def tick(self, human_approved: bool = False, audit_prob: float = 0.05) -> None:
        trace_id = str(uuid4())
        
        # 1. OBSERVE & ASSESS
        self.state = SICLState.OBSERVE
        world_state = self.sensor.read(self.t)
        self.state = SICLState.ASSESS
        dlog = self.dlog_calc.compute(world_state)
        self.last_dlog = dlog
        mode = self.gate.gate(dlog, type('obj', (object,), {'task_id':'dummy','type':'READ_ONLY_QUERY','e_est':0.0})).mode
        self.metrics.record_tick(mode)

        # 2. PLAN (Stasis Break Check)
        stasis_break = (self.metrics.ticks >= 8 and self.metrics.S_stasis >= 0.7)
        self.state = SICLState.PLAN
        tasks = self.planner.propose(dlog, world_state.observations, stasis_break)

        # 3. GATE (Candidate Rotation)
        self.state = SICLState.GATE
        chosen = None
        for cand in tasks:
            dec = self.gate.gate(dlog, cand, human_approved)
            if dec.action in ("ALLOW", "RESTRICT_ALLOW"):
                chosen = (cand, dec)
                break
        
        # Pre-commit Ledger
        self.ledger.append("pre_commit", {
            "t": self.t, "mode": mode, "chosen": chosen[0].__dict__ if chosen else None
        }, trace_id)

        # 4. ACT & REVIEW
        if chosen:
            self.state = SICLState.ACT
            res = self.executor.execute(chosen[0])
            self.metrics.record_action_weighted(chosen[0].type, chosen[0].payload, res.state_change_bits)
            
            self.state = SICLState.REVIEW
            # [Injection Point] Random Audit (Tau Controlled)
            if random.random() < audit_prob:
                self.ledger.append("sys_audit", {"trigger":"random", "prob":audit_prob}, trace_id)

            self.ledger.append("post_receipt", {"ok": res.ok, "bits": res.state_change_bits}, trace_id)
        else:
            self.ledger.append("post_receipt", {"skipped": True}, trace_id)

        self.state = SICLState.UPDATE
        self.metrics.record_closed_loop()
        self.t += 1
