import json
import os

class SoulMemory:
    def __init__(self, path="soul_memory.json"):
        self.path = path
        self.state = {
            "memories": []
        }
        self.load()

    def add_memory(self, memory: str):
        self.state["memories"].append(memory)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {"memories": []}
        else:
            self.state = {"memories": []}
