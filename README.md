# Smart To-Do List Agent

A multi-agent Smart To-Do List application in Python.

## Features
- Multi-agent pipeline: ParserAgent (LLM-style) → PriorityAgent (parallel) → SchedulerAgent (sequential)
- Custom tools: deadline extractor, priority detector
- Session (short-term) memory and long-term memory (persisted to JSON)
- Tkinter GUI with add/clear/export
- Observability: agent logs at logs/agent_logs.txt

## Run
```bash
python main.py
```

## Parking CCTV Security System
A standalone CCTV parking security prototype is available in `parking_cctv_system.py`.

Run:
```bash
python parking_cctv_system.py
```

It supports camera heartbeats, slot occupancy events, unauthorized reserved-slot detection, overstay alerts, and offline camera monitoring.
