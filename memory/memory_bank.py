# memory/memory_bank.py
import json
import os
from typing import Dict, List

class MemoryBank:
    """
    Long-term memory persisted to disk as JSON.
    Supports save, load, toggle done, delete, export.
    """
    def __init__(self, save_file="memory/memory_bank.json"):
        self.save_file = save_file
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        if not os.path.exists(save_file):
            with open(save_file, "w") as f:
                json.dump([], f)
        self._data = self._load_file()

    def _load_file(self):
        try:
            with open(self.save_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_file(self):
        with open(self.save_file, "w") as f:
            json.dump(self._data, f, indent=2)

    def save(self, task: Dict):
        # avoid duplicates: if id already exists, skip
        exists = any(t.get("id") == task.get("id") for t in self._data)
        if not exists:
            # ensure due is serializable
            self._data.append(task)
            self._save_file()
        return task

    def load_all(self) -> List[Dict]:
        self._data = self._load_file()
        return self._data

    def toggle_done(self, task_id: str):
        for t in self._data:
            if t.get("id") == task_id:
                t["done"] = not t.get("done", False)
                self._save_file()
                return t
        return None

    def delete(self, task_id: str):
        before = len(self._data)
        self._data = [t for t in self._data if t.get("id") != task_id]
        if len(self._data) < before:
            self._save_file()
            return True
        return False

    def export_json(self, outpath="memory/exported_tasks.json"):
        with open(outpath, "w") as f:
            json.dump(self._data, f, indent=2)
        return outpath
