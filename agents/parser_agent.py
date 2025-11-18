# agents/parser_agent.py
import re
import uuid
from datetime import datetime
from typing import List, Dict

class TaskParserAgent:
    """
    LLM-style Task Parser Agent.
    For demonstration we use heuristics + regex, but modelled as an LLM-powered agent.
    """
    def __init__(self, session=None):
        self.session = session

    def _split_into_chunks(self, text: str) -> List[str]:
        parts = re.split(r'\n|;|\.', text)
        parts = [p.strip() for p in parts if p.strip()]
        # further split when comma-separated but keep time-like commas ok
        return parts

    def _clean_title(self, part: str) -> str:
        # remove trailing deadline keywords (handled by deadline extractor)
        title = re.sub(r'\b(by|on|at)\s+[A-Za-z0-9: ]+\b', '', part, flags=re.I)
        # remove 'urgent' words to leave core title
        title = re.sub(r'\b(urgent|asap|immediately|important)\b', '', title, flags=re.I)
        return title.strip().strip(",-:;")

    def run(self, text: str):
        chunks = self._split_into_chunks(text)
        tasks = []
        for part in chunks:
            tasks.append({
                "id": uuid.uuid4().hex[:8],
                "title": self._clean_title(part) or part,
                "raw": part,
                "created_at": datetime.utcnow().isoformat(),
                "done": False
            })
        # push to session short-term memory
        if self.session:
            self.session.push_recent_tasks(tasks)
        return tasks
