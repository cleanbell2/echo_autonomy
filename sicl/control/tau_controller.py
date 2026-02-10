from __future__ import annotations
import math
from dataclasses import dataclass

def clip(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

@dataclass
class TauConfig:
    # 물리적 한계
    tau_min: float = 0.4; tau_max: float = 3.0
    dt_min: float = 0.4; dt_max: float = 3.0
    max_step: float = 0.2
    
    # 민감도 (Latency vs Decay)
    r_lat_target: float = 0.02
    r_dec_target: float = 0.35
    k_lat: float = 0.45
    k_dec: float = 0.35

    # 감사 확률 (절대 하한선 p_min 보장)
    p0: float = 0.10; p_min: float = 0.05; p_max: float = 0.60
    a_dec: float = 0.35; b_lat: float = 0.10

    # 쿨다운 (정체 시 감소, 위험 시 증가)
    cd0: float = 300.0; cd_min: float = 60.0; cd_max: float = 900.0
    c1_dec: float = 0.80; c2_stasis: float = 0.60

@dataclass
class TauOutputs:
    tau: float
    tick_interval_sec: float
    audit_prob: float
    stasis_cooldown_sec: float

class TauController:
    def __init__(self, cfg: TauConfig = None):
        self.cfg = cfg if cfg else TauConfig()
        self.tau = 1.0

    def compute(self, r_lat: float, r_dec: float, s_stasis: float) -> TauOutputs:
        c = self.cfg
        # Log-Linear Update
        log_tau = math.log(max(self.tau, 1e-6))
        # 지연되면(r_lat↑) 빨라지고, 오염되면(r_dec↑) 느려진다
        log_tau_next = log_tau + c.k_dec * (r_dec - c.r_dec_target) - c.k_lat * (r_lat - c.r_lat_target)
        
        tau_target = math.exp(clip(log_tau_next, math.log(c.tau_min), math.log(c.tau_max)))
        self.tau = self.tau + clip(tau_target - self.tau, -c.max_step, c.max_step)
        self.tau = clip(self.tau, c.tau_min, c.tau_max)

        tick_interval = clip(self.tau, c.dt_min, c.dt_max)
        
        # 감사 확률 계산
        p_audit = c.p0 + c.a_dec * r_dec - c.b_lat * r_lat
        p_audit = clip(p_audit, c.p_min, c.p_max)

        # 쿨다운 계산
        factor = (1.0 + c.c1_dec * r_dec) * (1.0 - c.c2_stasis * clip(s_stasis, 0.0, 1.0))
        cd = c.cd0 * factor
        if s_stasis > 0.9: cd = min(cd, 180.0) # 비상 탈출

        return TauOutputs(self.tau, tick_interval, p_audit, clip(cd, c.cd_min, c.cd_max))
