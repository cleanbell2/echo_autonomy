# sicl/world_sensor.py
from __future__ import annotations
import time
import threading
import queue
from typing import Any, Dict, Optional
from .types import WorldState

class InputListener(threading.Thread):
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
    def __init__(self, watch_files=None):
        self.watch_files = watch_files or []
        self._override: Dict[str, Any] = {}
        self.listener = InputListener()
        self.listener.start()
    
    def set_override(self, override: Optional[Dict[str, Any]]):
        self._override = override or {}
    
    def read(self, t: int) -> WorldState:
        user_in = None
        try:
            user_in = self.listener.input_queue.get_nowait()
        except queue.Empty:
            pass
        
        obs: Dict[str, Any] = {"time": time.time()}
        obs.update(self._override)
        
        return WorldState(t=t, observations=obs, user_input=user_in)
