import os
from .types import ActResult
class Executor:
    def __init__(self, out_dir="./artifacts"):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
    def execute(self, task):
        return ActResult(ok=True, state_change_bits=(1 if "WRITE" in task.type else 0))
