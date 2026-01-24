from .types import WorldState
import time
class WorldSensor:
    def __init__(self, watch_files=None): self.watch_files = watch_files or []
    def read(self, t): return WorldState(t, {"time": time.time()})
