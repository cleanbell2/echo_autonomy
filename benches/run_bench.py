import json, os, time, sys
# 꼼꼼하게: .env 자동 로드 (아까 준 코드 스타일 반영)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"✅ Env Loaded. MODEL={os.getenv('GEMINI_MODEL')}")
except ImportError:
    print("⚠️ Dotenv not found")

from sicl.state_machine import SICLStateMachine, DeltaLogCalculator
from sicl.world_sensor import WorldSensor
from sicl.planner import Planner
from sicl.gateway import GatewayNavigator
from sicl.executor import Executor
from sicl.ledger import AuditLedger
from sicl.control.tau_controller import TauController

def run_case(case):
    # Setup
    if os.path.exists("./audit_ledger.jsonl"): os.remove("./audit_ledger.jsonl")
    
    # Init Modules
    tau_ctrl = TauController()
    sm = SICLStateMachine(
        WorldSensor(), DeltaLogCalculator(), Planner(), 
        GatewayNavigator(), Executor(), AuditLedger()
    )

    # Force Setup
    force_dlog = case.get("setup", {}).get("force_dlog")
    sim_lat = case.get("setup", {}).get("simulate_latency", 0.0)

    # Run Ticks (Tau Loop Simulation)
    taus, audit_probs, cooldowns = [], [], []
    
    for _ in range(case.get("steps", [])[0].get("run_ticks", 5)):
        # 1. Tau Compute
        r_lat = sim_lat # Mock latency
        r_dec = 0.8 if force_dlog else 0.0
        s_stasis = sm.metrics.S_stasis
        
        outs = tau_ctrl.compute(r_lat, r_dec, s_stasis)
        
        # 2. Injection
        sm.planner.set_runtime_controls(outs.stasis_cooldown_sec)
        sm.tick(audit_prob=outs.audit_prob)
        
        # Record
        taus.append(outs.tau)
        audit_probs.append(outs.audit_prob)
        cooldowns.append(outs.stasis_cooldown_sec)

    return sm.metrics, {"taus": taus, "audits": audit_probs, "cds": cooldowns}

def main():
    with open("benches/autonomybench20.jsonl", "r") as f:
        cases = [json.loads(l) for l in f if l.strip()]
    
    print("\n🚀 Running AutonomyBench-25 (with Tau Controller)...\n")
    for c in cases:
        m, data = run_case(c)
        print(f"[{c['id']:02d}] {c['name']:<30} | A_gain: {m.A_gain:.2f} | Tau_End: {data['taus'][-1]:.2f}")

if __name__ == "__main__":
    main()
