# memory/session_memory.py
from collections import deque
import time

class InMemorySessionService:
    """
    Short-term session memory. Keeps recent inputs and recent tasks.
    """
    def __init__(self, max_inputs=20, max_recent_tasks=50):
        self.inputs = deque(maxlen=max_inputs)  # raw user inputs
        self.recent_tasks = deque(maxlen=max_recent_tasks)
        self.created_at = time.time()

    def push_user_input(self, text):
        self.inputs.appendleft({"text": text, "ts": time.time()})

    def push_agent_response(self, name, response):
        self.inputs.appendleft({"agent": name, "response": response, "ts": time.time()})

    def push_recent_tasks(self, tasks):
        for t in tasks:
            self.recent_tasks.appendleft(t)

    def get_recent_inputs(self):
        return list(self.inputs)

    def get_recent_tasks(self):
        return list(self.recent_tasks)
