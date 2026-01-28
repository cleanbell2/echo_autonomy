from dataclasses import dataclass, field, asdict
import time
import json
import threading
import numpy as np
from typing import List, Union, Optional, Dict
from .threshold import DynamicThreshold

@dataclass
class EBreakMetrics:
    e_break_value: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

@dataclass
class MonitoringSession:
    session_id: str
    start_time: float

class EBreakMonitor:
    def __init__(self, session_duration=None, threshold=0.85, threshold_system=None):
        self.is_monitoring = False
        self.current_session: Optional[MonitoringSession] = None
        self.threshold_system = threshold_system if threshold_system else DynamicThreshold(base_threshold=threshold)
        self.metrics_buffer: List[EBreakMetrics] = []
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.total_metrics_processed = 0
        self.total_alerts_generated = 0
        self.total_interventions_recommended = 0
        self.alert_callback = None

    def start_monitoring(self, session_id: str):
        if self.is_monitoring:
            raise RuntimeError("Monitoring already active")
        self.is_monitoring = True
        self.current_session = MonitoringSession(session_id, time.time())
        if not self.metrics_buffer:
            self.metrics_buffer = []

    def add_metrics(self, metrics: Union[EBreakMetrics, float, List]):
        items = []
        if isinstance(metrics, (int, float)):
            items.append(EBreakMetrics(e_break_value=float(metrics)))
        elif isinstance(metrics, list):
            items.extend(metrics)
        else:
            items.append(metrics)
        for item in items:
            self.metrics_buffer.append(item)
            self.total_metrics_processed += 1
            if self.alert_callback:
                data = {"e_break_value": item.e_break_value, "theta_integrity": 1.0 - item.e_break_value}
                self.alert_callback(data)

    def stop_monitoring(self):
        self.is_monitoring = False
        stats = self.get_monitoring_statistics()
        stats["status"] = "completed"
        return stats

    def get_monitoring_statistics(self):
        values = [m.e_break_value for m in self.metrics_buffer]
        anomalies = len([v for v in values if v > 1.5])
        return {
            "session_id": self.current_session.session_id if self.current_session else None,
            "buffer_statistics": {"anomalies_detected": anomalies, "count": len(values)},
            "threshold_stats": self.threshold_system.get_threshold_statistics()
        }

    def export_session_data(self, filename: str):
        data = {
            "session_info": {
                "session_id": self.current_session.session_id if self.current_session else "unknown"
            },
            "metrics": [asdict(m) for m in self.metrics_buffer]
        }
        with open(filename, "w") as f:
            json.dump(data, f)

def create_monitoring_dashboard(monitor):
    return f"BCDSI MONITORING DASHBOARD\nStatus: Active\nStats: {monitor.get_monitoring_statistics()}"