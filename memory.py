"""Long-term memory: stores summaries of past tasks in a JSON file."""
import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join("data", "memory.json")


class Memory:
    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            self._write([])

    def _read(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add(self, task: str, summary: str):
        data = self._read()
        data.append({"time": datetime.now().isoformat(timespec="seconds"),
                     "task": task, "summary": summary})
        self._write(data[-50:])  # keep last 50

    def recent(self, n: int = 3) -> str:
        items = self._read()[-n:]
        if not items:
            return "No previous tasks."
        return "\n".join(f"- [{i['time']}] {i['task']} -> {i['summary']}" for i in items)
