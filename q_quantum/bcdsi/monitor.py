import threading
import time
import numpy as np
from datetime import datetime

class EBreakMonitor:
    """
    실시간 양자 브레이크 지수 및 무결성 모니터링
    (시스템의 '심박수'를 체크하는 스레드)
    """
    def __init__(self, threshold=0.85):
        self.threshold = threshold
        self.is_running = False
        self._lock = threading.Lock()
        self.logs = []
        self._stop_event = threading.Event()

    def start(self):
        """모니터링 시작"""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        print(f"📡 [Monitor] EBreak Monitoring Started (Threshold: {self.threshold})")

    def stop(self):
        """모니터링 중지"""
        self.is_running = False
        self._stop_event.set()
        print("📡 [Monitor] EBreak Monitoring Stopped")

    def analyze_trend(self, current_val):
        """
        현재 값을 기록하고 임계값 초과 여부 리턴
        """
        with self._lock:
            # 로그는 최근 100개만 유지 (메모리 보호)
            if len(self.logs) > 100:
                self.logs.pop(0)
            
            self.logs.append({"ts": datetime.now(), "val": current_val})
            
            # 단순 임계값 초과 체크
            is_overflow = current_val > self.threshold
            
            return is_overflow
