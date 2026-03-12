# Smart To-Do List Agent

A multi-agent Smart To-Do List application in Python.

## Features
- Multi-agent pipeline: ParserAgent (LLM-style) → PriorityAgent (parallel) → SchedulerAgent (sequential)
- Additional SocialMediaContentAgent for generating platform-specific post variants
- Custom tools: deadline extractor, priority detector
- Session (short-term) memory and long-term memory (persisted to JSON)
- Tkinter GUI with add/clear/export
- Observability: agent logs at logs/agent_logs.txt

## Run
```bash
python main.py
```

## Social media content agent example
```python
from agents.social_media_agent import SocialMediaContentAgent, ContentRequest

agent = SocialMediaContentAgent()
result = agent.run(ContentRequest(
    topic="behind-the-scenes product launch tips",
    platform="instagram",
    audience="indie founders",
    tone="confident",
    call_to_action="Comment 'LAUNCH' if you want the checklist.",
    max_variants=2,
))

print(result["variants"])
```
