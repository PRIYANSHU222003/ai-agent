# tools/priority_detector.py
import re

class PriorityDetectorTool:
    """
    Detects priority words in text:
    - High for urgent/asap/immediately/important
    - Medium for soon / this week
    - Normal otherwise
    """
    HIGH = re.compile(r'\b(urgent|asap|immediately|important|priority)\b', re.I)
    MEDIUM = re.compile(r'\b(soon|this week|by end of week|by friday|by monday)\b', re.I)

    def detect(self, text: str) -> str:
        if self.HIGH.search(text):
            return "High"
        if self.MEDIUM.search(text):
            return "Medium"
        return "Normal"
