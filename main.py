# main.py
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from agents.parser_agent import TaskParserAgent
from agents.priority_agent import PriorityAgent
from agents.scheduler_agent import SchedulerAgent
from memory.session_memory import InMemorySessionService
from memory.memory_bank import MemoryBank
import logging
from datetime import datetime

# ensure folders
os.makedirs("logs", exist_ok=True)
os.makedirs("memory", exist_ok=True)

# Logging (observability)
logging.basicConfig(
    filename="logs/agent_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log(agent_name, input_data, output_data):
    logging.info(f"{agent_name} | INPUT: {input_data} | OUTPUT: {output_data}")

# Initialize components
session = InMemorySessionService()
memory = MemoryBank(save_file="memory/memory_bank.json")

parser_agent = TaskParserAgent(session=session)
priority_agent = PriorityAgent()
scheduler_agent = SchedulerAgent(memory=memory)

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Smart To-Do List Agent")
root.geometry("760x580")
root.resizable(False, False)

title = tk.Label(root, text="Smart To-Do List Agent", font=("Segoe UI", 20, "bold"))
title.pack(pady=10)

input_frame = tk.Frame(root)
input_frame.pack(padx=12, pady=6, fill="x")

lbl = tk.Label(input_frame, text="Enter tasks (separate with ';' or newline):", font=("Segoe UI", 10))
lbl.pack(anchor="w")

text_input = tk.Text(input_frame, height=5, width=90, font=("Segoe UI", 11))
text_input.pack(pady=6)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=6)

def process_and_show():
    raw = text_input.get("1.0", tk.END).strip()
    if not raw:
        messagebox.showwarning("No input", "Please type some tasks first.")
        return

    # 1. Parse via TaskParserAgent (LLM-style)
    parsed = parser_agent.run(raw)
    log("TaskParserAgent", raw, parsed)

    # 2. PriorityAgent (parallel subagents)
    prioritized = priority_agent.run(parsed)
    log("PriorityAgent", parsed, prioritized)

    # 3. SchedulerAgent (sequential)
    scheduled = scheduler_agent.run(prioritized)
    log("SchedulerAgent", prioritized, scheduled)

    # update session
    session.push_user_input(raw)
    session.push_agent_response("pipeline", scheduled)

    # refresh UI
    refresh_task_list()

def refresh_task_list():
    # display memory long-term tasks
    for widget in task_display_frame.winfo_children():
        widget.destroy()

    tasks = memory.load_all()
    if not tasks:
        tk.Label(task_display_frame, text="No tasks saved yet.", font=("Segoe UI", 11)).pack(anchor="w", padx=8, pady=6)
        return

    for t in tasks:
        card = tk.Frame(task_display_frame, bd=1, relief="solid", padx=8, pady=6)
        card.pack(fill="x", padx=6, pady=6)

        top = tk.Frame(card)
        top.pack(fill="x")
        tk.Label(top, text=t.get("title", ""), font=("Segoe UI", 12, "bold")).pack(side="left", anchor="w")
        status = "Done" if t.get("done") else "Open"
        tk.Label(top, text=status, font=("Segoe UI", 10)).pack(side="right")

        info = f"Due: {t.get('due')}  |  Priority: {t.get('priority')}  |  ID: {t.get('id')}"
        tk.Label(card, text=info, font=("Segoe UI", 10)).pack(anchor="w")

        btns = tk.Frame(card)
        btns.pack(anchor="e", pady=4)
        def make_toggle(task_id):
            def toggle():
                memory.toggle_done(task_id)
                refresh_task_list()
            return toggle

        def make_delete(task_id):
            def delete():
                memory.delete(task_id)
                refresh_task_list()
            return delete

        tk.Button(btns, text="Toggle Done", command=make_toggle(t["id"]), width=12).pack(side="left", padx=4)
        tk.Button(btns, text="Delete", command=make_delete(t["id"]), width=8).pack(side="left", padx=4)

# Buttons
add_btn = tk.Button(btn_frame, text="Parse & Add Tasks", command=process_and_show, bg="#2e86de", fg="white", width=18)
add_btn.grid(row=0, column=0, padx=6)

clear_input_btn = tk.Button(btn_frame, text="Clear Input", command=lambda: text_input.delete("1.0", tk.END), width=12)
clear_input_btn.grid(row=0, column=1, padx=6)

refresh_btn = tk.Button(btn_frame, text="Refresh Task List", command=refresh_task_list, width=14)
refresh_btn.grid(row=0, column=2, padx=6)

export_btn = tk.Button(btn_frame, text="Export Tasks (JSON)", command=lambda: memory.export_json("memory/exported_tasks.json"), width=16)
export_btn.grid(row=0, column=3, padx=6)

# Task list area (scrollable)
container = tk.Frame(root)
container.pack(fill="both", expand=True, padx=12, pady=6)

canvas = tk.Canvas(container, height=350)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
task_display_frame = tk.Frame(canvas)

task_display_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0, 0), window=task_display_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# status bar
status_bar = tk.Label(root, text=f"Loaded tasks: {len(memory.load_all())}  |  Session inputs: {len(session.inputs)}", bd=1, relief="sunken", anchor="w")
status_bar.pack(fill="x", side="bottom")

def update_status():
    status_bar.config(text=f"Loaded tasks: {len(memory.load_all())}  |  Session inputs: {len(session.inputs)}")
    root.after(1000, update_status)

update_status()
refresh_task_list()
root.mainloop()
