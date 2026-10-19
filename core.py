"""Agent core: Planner -> Executor (ReAct tool loop) -> Reflector."""
import json
import os

import anthropic

from .memory import Memory
from .tools import TOOL_SCHEMAS, run_tool

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_STEPS = 10


class ResearchAgent:
    def __init__(self, verbose: bool = True):
        self.client = anthropic.Anthropic()
        self.memory = Memory()
        self.verbose = verbose

    def _log(self, tag, msg):
        if self.verbose:
            print(f"\n[{tag}] {msg}")

    @staticmethod
    def _text(resp) -> str:
        return "".join(b.text for b in resp.content if b.type == "text")

    # ---- 1. PLANNER ----
    def plan(self, task: str) -> list:
        resp = self.client.messages.create(
            model=MODEL, max_tokens=600,
            system="You are a planner. Break the task into 2-5 short, concrete steps. "
                   "Available tools: calculator, wikipedia_search, save_note, read_note, "
                   "list_notes, get_datetime. Reply ONLY with a JSON list of strings.",
            messages=[{"role": "user", "content": task}])
        raw = self._text(resp).replace("```json", "").replace("```", "").strip()
        try:
            steps = json.loads(raw)
        except json.JSONDecodeError:
            steps = [task]
        self._log("PLAN", "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)))
        return steps

    # ---- 2. EXECUTOR ----
    def execute(self, task: str, steps: list) -> str:
        system = ("You are an autonomous research agent. Follow the plan, use tools when "
                  "needed, and give a clear final answer. Never invent facts; use tools.\n\n"
                  f"PAST TASKS (memory):\n{self.memory.recent()}")
        plan_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        messages = [{"role": "user", "content": f"Task: {task}\n\nPlan:\n{plan_text}"}]

        for _ in range(MAX_STEPS):
            resp = self.client.messages.create(
                model=MODEL, max_tokens=1500, system=system,
                tools=TOOL_SCHEMAS, messages=messages)
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                return self._text(resp)

            results = []
            for block in resp.content:
                if block.type == "tool_use":
                    self._log("ACT", f"{block.name}({json.dumps(block.input)})")
                    out = run_tool(block.name, block.input)
                    self._log("OBSERVE", out[:300])
                    results.append({"type": "tool_result",
                                    "tool_use_id": block.id, "content": out})
            messages.append({"role": "user", "content": results})
        return "Stopped: maximum steps reached."

    # ---- 3. REFLECTOR ----
    def reflect(self, task: str, answer: str) -> str:
        resp = self.client.messages.create(
            model=MODEL, max_tokens=1200,
            system="You are a critic. Check if the answer fully completes the task and is "
                   "accurate. If good, return it unchanged; otherwise return an improved "
                   "version. Output only the final answer.",
            messages=[{"role": "user",
                       "content": f"Task: {task}\n\nDraft answer:\n{answer}"}])
        return self._text(resp)

    def run(self, task: str) -> str:
        steps = self.plan(task)
        draft = self.execute(task, steps)
        final = self.reflect(task, draft)
        self.memory.add(task, final[:200].replace("\n", " "))
        return final
