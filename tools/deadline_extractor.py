# tools/deadline_extractor.py
import re
from datetime import datetime, timedelta
import calendar

class DeadlineExtractorTool:
    """
    Simple deadline extractor:
    - recognizes 'today', 'tomorrow', 'tonight'
    - 'at 6pm', 'at 18:00', '6pm'
    - 'on Monday', 'next Tuesday'
    - 'by Friday', 'by 5pm'
    Returns either ISO datetime string or friendly string.
    """

    WEEKDAYS = {name.lower(): idx for idx, name in enumerate(calendar.day_name)}  # Monday=0

    def _next_weekday(self, target_weekday: int):
        today = datetime.now()
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def extract(self, text: str):
        txt = text.lower()

        # direct keywords
        if re.search(r'\btomorrow\b', txt):
            base = datetime.now() + timedelta(days=1)
            time = self._extract_time(txt)
            if time:
                dt = base.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
                return dt.isoformat()
            return (base.replace(hour=23, minute=59)).isoformat()

        if re.search(r'\btoday\b', txt) or re.search(r'\btonight\b', txt):
            base = datetime.now()
            time = self._extract_time(txt)
            if time:
                dt = base.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
                return dt.isoformat()
            return (base.replace(hour=23, minute=59)).isoformat()

        # weekday names
        m = re.search(r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', txt)
        if m:
            wd = m.group(1)
            target = self.WEEKDAYS.get(wd, None)
            if target is not None:
                base = self._next_weekday(target)
                time = self._extract_time(txt)
                if time:
                    dt = base.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
                    return dt.isoformat()
                return base.replace(hour=23, minute=59).isoformat()

        # by X / by Friday / by 5pm
        m2 = re.search(r'\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(:\d{2})?\s*(am|pm)?)\b', txt)
        if m2:
            token = m2.group(1)
            if token in self.WEEKDAYS:
                base = self._next_weekday(self.WEEKDAYS[token])
                return base.replace(hour=23, minute=59).isoformat()
            # time like '5pm'
            time = self._parse_time_token(token)
            if time:
                base = datetime.now()
                dt = base.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
                return dt.isoformat()

        # direct time 'at 6pm' or '6pm'
        time = self._extract_time(txt)
        if time:
            base = datetime.now()
            dt = base.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
            return dt.isoformat()

        return None

    def _extract_time(self, txt: str):
        # pattern: at 6pm, at 18:30, 6pm, 6:30pm
        m = re.search(r'\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', txt)
        if m:
            return self._parse_time_token(m.group(0))
        m2 = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', txt)
        if m2:
            return self._parse_time_token(m2.group(0))
        return None

    def _parse_time_token(self, token: str):
        token = token.strip()
        m = re.match(r'.*?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', token)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if ampm:
            if ampm.lower() == 'pm' and hour != 12:
                hour += 12
            if ampm.lower() == 'am' and hour == 12:
                hour = 0
        return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
