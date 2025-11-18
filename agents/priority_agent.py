# agents/priority_agent.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools.deadline_extractor import DeadlineExtractorTool
from tools.priority_detector import PriorityDetectorTool
from typing import List, Dict

class PriorityAgent:
    """
    Runs two sub-agents in parallel:
    - deadline extraction
    - priority detection
    Merges results into task objects.
    """
    def __init__(self):
        self.deadline_tool = DeadlineExtractorTool()
        self.priority_tool = PriorityDetectorTool()

    def _run_deadline(self, task):
        return self.deadline_tool.extract(task["raw"])

    def _run_priority(self, task):
        return self.priority_tool.detect(task["raw"])

    def run(self, tasks: List[Dict]):
        enhanced = []
        with ThreadPoolExecutor(max_workers=4) as ex:
            # submit both tools for each task
            futures = {}
            for t in tasks:
                futures[ex.submit(self._run_deadline, t)] = ("deadline", t)
                futures[ex.submit(self._run_priority, t)] = ("priority", t)

            # temp store
            temp = {t["id"]: {"title": t["title"], "raw": t["raw"], "id": t["id"], "created_at": t.get("created_at")} for t in tasks}
            for fut in as_completed(futures):
                typ, task = futures[fut]
                result = fut.result()
                if typ == "deadline":
                    temp[task["id"]]["due"] = result
                else:
                    temp[task["id"]]["priority"] = result

            # produce list
            for tid, obj in temp.items():
                # set defaults if missing
                obj.setdefault("due", None)
                obj.setdefault("priority", "Normal")
                obj.setdefault("done", False)
                enhanced.append(obj)
        return enhanced
