from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

class InterventionLevel(Enum):
    MONITOR = "monitor"
    WARNING = "warning"
    MODIFY = "modify"
    BLOCK = "block"

@dataclass
class InterventionRecord:
    e_break_value: float
    theta_integrity: float
    threshold: float
    intervention_level: InterventionLevel
    timestamp: float = field(default_factory=time.time)
    action: str = "monitor"
    context: Optional[Dict] = None

    @property
    def action_taken(self) -> str:
        if self.intervention_level == InterventionLevel.BLOCK:
            return "BLOCK_EXECUTION"
        return self.action

    @property
    def effectiveness_score(self) -> float:
        return self.theta_integrity * 0.9 + 0.1

def intervene(e_break: float, theta: float, threshold: float, context: Optional[Dict] = None) -> InterventionRecord:
    diff = e_break - threshold
    if diff <= 0:
        level = InterventionLevel.MONITOR
        action = "MONITOR"
    elif diff < 0.1:
        level = InterventionLevel.WARNING
        action = "LOG_WARNING"
    elif diff < 0.5:
        level = InterventionLevel.MODIFY
        action = "ADJUST_PARAMETERS"
    else:
        level = InterventionLevel.BLOCK
        action = "HALT_EXECUTION"
    return InterventionRecord(e_break, theta, threshold, level, action=action, context=context)

def format_intervention_message(record: InterventionRecord) -> str:
    return f"[{record.intervention_level.value.upper()}] E-Break: {record.e_break_value:.3f} | Action: {record.action}"

class BCDSIInterventionHistory:
    def __init__(self, max_history=100):
        self.records: List[InterventionRecord] = []
        self.max_history = max_history
        self.intervention_counts = {lvl: 0 for lvl in InterventionLevel}

    def add_record(self, record: InterventionRecord) -> None:
        self.records.append(record)
        if len(self.records) > self.max_history:
            self.records.pop(0)
        self.intervention_counts[record.intervention_level] += 1

    def get_pattern_analysis(self) -> Dict[str, Any]:
        return {
            "total_records": len(self.records),
            "trend": "stable" if self.intervention_counts[InterventionLevel.BLOCK] == 0 else "critical"
        }

class BcdsiIntervenor:
    def intervene(self, *args, **kwargs):
        return intervene(*args, **kwargs)
