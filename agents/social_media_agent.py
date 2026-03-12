from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import re


@dataclass
class ContentRequest:
    topic: str
    platform: str = "instagram"
    audience: str = "general"
    tone: str = "friendly"
    call_to_action: str = "Share your thoughts in the comments."
    max_variants: int = 3


class SocialMediaContentAgent:
    """
    Agent for generating short-form social media post variants.

    The agent is template-driven so it can run locally without external APIs.
    """

    _PLATFORM_LIMITS = {
        "x": 280,
        "twitter": 280,
        "linkedin": 3000,
        "instagram": 2200,
        "facebook": 63206,
    }

    _HOOKS = [
        "Quick idea:",
        "Today\'s takeaway:",
        "If you\'re working on this, read this:",
        "A simple strategy that works:",
    ]

    def _normalize_platform(self, platform: str) -> str:
        p = (platform or "instagram").strip().lower()
        return "x" if p == "twitter" else p

    def _build_hashtags(self, topic: str, audience: str) -> List[str]:
        words = re.findall(r"[A-Za-z0-9]+", f"{topic} {audience}".lower())
        cleaned = [w for w in words if len(w) > 3]
        uniq = []
        for w in cleaned:
            if w not in uniq:
                uniq.append(w)
        hashtags = [f"#{w}" for w in uniq[:5]]
        if "#content" not in hashtags:
            hashtags.append("#content")
        return hashtags

    def _trim_for_platform(self, text: str, platform: str) -> str:
        limit = self._PLATFORM_LIMITS.get(platform, 2200)
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def run(self, request: ContentRequest) -> Dict:
        platform = self._normalize_platform(request.platform)
        hashtags = self._build_hashtags(request.topic, request.audience)

        variants = []
        for idx in range(max(1, request.max_variants)):
            hook = self._HOOKS[idx % len(self._HOOKS)]
            body = (
                f"{hook} {request.topic} for {request.audience}. "
                f"Keep it {request.tone}, actionable, and outcome-focused. "
                f"{request.call_to_action}"
            )
            if platform in {"instagram", "x", "facebook"}:
                body = f"{body}\n\n{' '.join(hashtags)}"

            variants.append(self._trim_for_platform(body, platform))

        return {
            "created_at": datetime.utcnow().isoformat(),
            "platform": platform,
            "topic": request.topic,
            "audience": request.audience,
            "tone": request.tone,
            "variants": variants,
            "hashtags": hashtags,
            "character_limit": self._PLATFORM_LIMITS.get(platform, 2200),
        }
