import numpy as np
from enum import Enum
from typing import List, Dict, Union, Optional

class PolicyType(Enum):
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"

class SystemCriticality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class DynamicThreshold:
    def __init__(self, base_threshold=0.85, policy=PolicyType.MODERATE, 
                 min_threshold=0.1, max_threshold=0.95, 
                 adaptation_rate=0.1, history_window=50):
        self.base_threshold = base_threshold
        self.current_threshold = base_threshold
        self.policy = policy
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.adaptation_rate = adaptation_rate
        self.history_window = history_window
        self.threshold_history = [] 

    def set_policy(self, policy: PolicyType):
        self.policy = policy

    def _update_threshold(self, integrity_val: float):
        if integrity_val > 0.8:
            self.current_threshold = min(self.max_threshold, self.current_threshold + 0.01)
        else:
            self.current_threshold = max(self.min_threshold, self.current_threshold - 0.01)
        self.threshold_history.append(self.current_threshold)

    def get_system_criticality(self, metrics: Dict) -> SystemCriticality:
        error_rate = metrics.get("error_rate", 0.0)
        latency = metrics.get("latency", 0.0)
        if error_rate > 0.1 or latency > 50.0:
            return SystemCriticality.HIGH
        elif error_rate > 0.05:
            return SystemCriticality.MEDIUM
        return SystemCriticality.LOW

    def calculate_theta_integrity(self, e_break_value, vn_entropy=0.0, coherence=0.0, 
                                  non_unitarity=0.0, theta_history=None, 
                                  policy=None, system_criticality=None, adaptation_window=None,
                                  historical_theta=None):
        policy_impact = 0.0
        current_policy = policy or self.policy
        if current_policy == PolicyType.AGGRESSIVE:
            policy_impact = -0.1
        elif current_policy == PolicyType.CONSERVATIVE:
            policy_impact = 0.1
        base_integrity = max(0.0, 1.0 - e_break_value + policy_impact)
        if historical_theta is not None:
             self._update_threshold(base_integrity)
        return base_integrity

    def get_threshold_statistics(self) -> Dict:
        if not self.threshold_history:
            return {"mean": self.base_threshold, "std": 0.0}
        return {
            "mean": float(np.mean(self.threshold_history)),
            "std": float(np.std(self.threshold_history)),
            "current": self.current_threshold
        }

def calculate_theta_integrity(*args, **kwargs):
    dt = DynamicThreshold()
    return dt.calculate_theta_integrity(*args, **kwargs)

def create_policy_based_threshold(policy: PolicyType) -> DynamicThreshold:
    return DynamicThreshold(policy=policy)
