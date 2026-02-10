from .types import WorldState
import time
import threading
import queue

class InputListener(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.input_queue = queue.Queue()
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            try:
                user_in = input()
                self.input_queue.put(user_in)
            except EOFError:
                break

    def stop(self):
        self._stop.set()

class WorldSensor:
    def __init__(self, watch_files=None):
        self.watch_files = watch_files or []
        self.listener = InputListener()
        self.listener.start()

    def read(self, t):
        user_input = None
        if not self.listener.input_queue.empty():
            user_input = self.listener.input_queue.get()
        return WorldState(t, {"time": time.time(), "user_input": user_input}, user_input=user_input)
