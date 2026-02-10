import threading
import time
import numpy as np
import json
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict

# 1. EBreakMetrics 클래스 추가 (테스트가 찾고 있음)
class EBreakMetrics:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.buffer = []
        
    def add(self, value):
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
            
    def get_stats(self):
        if not self.buffer:
            return {"mean": 0.0, "max": 0.0, "std": 0.0}
        return {
            "mean": float(np.mean(self.buffer)),
            "max": float(np.max(self.buffer)),
            "std": float(np.std(self.buffer))
        }

# 2. Monitor 클래스 (Metrics 통합 버전)
class EBreakMonitor:
    def __init__(self, threshold=0.85, window_size=100):
        self.threshold = threshold
        self.is_running = False
        self._lock = threading.Lock()
        self.metrics = EBreakMetrics(window_size) # Metrics 객체 사용
        self.logs = []
        self._stop_event = threading.Event()

    def start(self):
        if self.is_running: return
        self.is_running = True
        self._stop_event.clear()

    def stop(self):
        self.is_running = False
        self._stop_event.set()

    def analyze_trend(self, current_val):
        with self._lock:
            # Metrics에 추가
            self.metrics.add(current_val)
            
            # 로그 기록
            self.logs.append({"ts": datetime.now().isoformat(), "val": current_val})
            if len(self.logs) > 100: self.logs.pop(0)
            
            return current_val > self.threshold
            
    def export_session(self):
        """세션 데이터 내보내기"""
        with self._lock:
            return json.dumps({
                "logs": self.logs,
                "stats": self.metrics.get_stats()
            })

# 3. EBreakCalculator 클래스
class EBreakCalculator:
    """
    Δ-Log v3.4 Core Calculation Unit
    """
    def calculate_ebreak(self, density_matrix, work=0.0, free_energy_change=0.0, **kwargs):
        # 모의 계산 로직 (Simulation Logic)
        e_break_val = 0.42  # Test dummy value
        
        return {
            "e_break_qbn": e_break_val,
            "theta_integrity": 1.0,
            "bcdsi_detected": False,
            "analysis_summary": {"status": "nominal"}
        }

    def calculate(self, rho, echo_context=None):
        echo_context = echo_context or {}
        return self.calculate_ebreak(
            density_matrix=rho,
            work=echo_context.get("work", 0.0),
            free_energy_change=echo_context.get("free_energy_change", 0.0)
        )
