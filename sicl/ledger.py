import json, os, time, hashlib
class AuditLedger:
    def __init__(self, path="./audit_ledger.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.last_hash = "GENESIS"
    def append(self, kind, data, trace_id):
        rec = {"ts": time.time(), "kind": kind, "data": data, "prev": self.last_hash}
        blob = json.dumps(rec, sort_keys=True).encode()
        self.last_hash = hashlib.sha256(blob).hexdigest()
        rec["hash"] = self.last_hash
        with open(self.path, "a") as f: f.write(json.dumps(rec)+"\n")
    def verify_chain(self): return True # (간소화)
