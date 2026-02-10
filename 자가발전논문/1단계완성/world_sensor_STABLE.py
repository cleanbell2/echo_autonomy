# sicl/world_sensor.py (실행 가능 v2.1)
from __future__ import annotations
import time
import threading
import queue
from typing import Any, Dict, Optional
from .types import WorldState


class InputListener(threading.Thread):
    """비동기 입력 리스너 - 메인 루프를 멈추지 않음"""

    def __init__(self):
        super().__init__(daemon=True)
        self.input_queue = queue.Queue()

    def run(self):
        while True:
            try:
                u = input()
                if u.strip():
                    self.input_queue.put(u.strip())
            except (EOFError, KeyboardInterrupt):
                break
            except Exception:
                pass


class WorldSensor:
    """환경 관측 + 사용자 입력 감지"""

    def __init__(self, watch_files=None):
        self.watch_files = watch_files or []
        self._override: Dict[str, Any] = {}
        self.listener = InputListener()
        self.listener.start()

    def set_override(self, override: Optional[Dict[str, Any]]):
        """벤치마크용 설정 주입"""
        self._override = override or {}

    def read(self, t: int) -> WorldState:
        """Non-blocking 입력 체크"""
        user_in = None
        try:
            user_in = self.listener.input_queue.get_nowait()
        except queue.Empty:
            pass

        obs: Dict[str, Any] = {"time": time.time()}
        obs.update(self._override)

        # ← 벨님 지적: 여기가 끊겼었음, 완전 복구
        return WorldState(
            t=t,
            observations=obs,
            user_input=user_in
        )
