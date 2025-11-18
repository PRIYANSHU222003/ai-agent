# agents/scheduler_agent.py
from memory.memory_bank import MemoryBank
from datetime import datetime
from typing import List, Dict
import logging

class SchedulerAgent:
    """
    Sequential agent that orders tasks and stores them in long-term memory.
    """
    def __init__(self, memory: MemoryBank):
        self.memory = memory

    def _sort_key(self, task: Dict):
        # high priority first, then by due date (None last)
        pr = 0 if task.get("priority", "Normal").lower() == "high" else 1
        due = task.get("due")
        try:
            if isinstance(due, str):
                # try JSON-serialized ISO string
                return (pr, datetime.fromisoformat(due))
            return (pr, due or datetime.max)
        except Exception:
            return (pr, datetime.max)

    def run(self, tasks: List[Dict]):
        # Sort tasks
        tasks_sorted = sorted(tasks, key=self._sort_key)
        # Save to memory bank
        for t in tasks_sorted:
            self.memory.save(t)
        return tasks_sorted
