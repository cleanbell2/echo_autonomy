from q_quantum import EBreakCalculator
import json, time

class EchoGovernanceBridge:
    def __init__(self, ledger_path="audit_ledger.jsonl"):
        self.core = EBreakCalculator()
        self.ledger_path = ledger_path

    def run_check(self, rho, echo_context):
        """
        echo_context: {'status': ..., 'memory_node': ..., 'psi': ...}
        """
        # [LOCK] 오직 이 엔트리포인트만 호출
        report = self.core.calculate_ebreak(rho, echo_context)
        
        # [Audit Ledger] 한 줄 기록 규약
        log_entry = {
            "ts": time.time(),
            "action": "INTERVENE" if report["bcdsi_detected"] else "PASS",
            "q_val": report["e_break_qbn"],
            "theta": report["theta_integrity"],
            "msg": report["analysis_summary"],
            "ctx": echo_context.get("status", "idle")
        }
        
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
        return report
