"""Tools the agent can call. Each tool = JSON schema + Python function."""
import ast
import operator as op
import os
from datetime import datetime

NOTES_DIR = os.path.join("data", "notes")

# ---------- safe calculator ----------
_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.FloorDiv: op.floordiv}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


# ---------- wikipedia search ----------
def wikipedia_search(query: str) -> str:
    import requests
    hdr = {"User-Agent": "AgenticResearchAgent/1.0"}
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", timeout=10, headers=hdr,
                         params={"action": "query", "list": "search", "srsearch": query,
                                 "format": "json", "srlimit": 1})
        hits = r.json()["query"]["search"]
        if not hits:
            return "No results found."
        title = hits[0]["title"]
        s = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/"
                         + title.replace(" ", "_"), timeout=10, headers=hdr).json()
        return f"{title}: {s.get('extract', 'No summary available.')}"
    except Exception as e:
        return f"Error: {e}"


# ---------- notes (file I/O) ----------
def _safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in "-_") + ".md"


def save_note(title: str, content: str) -> str:
    os.makedirs(NOTES_DIR, exist_ok=True)
    path = os.path.join(NOTES_DIR, _safe_name(title))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved note to {path}"


def read_note(title: str) -> str:
    path = os.path.join(NOTES_DIR, _safe_name(title))
    if not os.path.exists(path):
        return "Note not found."
    with open(path, encoding="utf-8") as f:
        return f.read()


def list_notes() -> str:
    if not os.path.isdir(NOTES_DIR):
        return "No notes yet."
    return "\n".join(os.listdir(NOTES_DIR)) or "No notes yet."


def get_datetime() -> str:
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")


# ---------- registry ----------
def _schema(name, desc, props, required):
    return {"name": name, "description": desc,
            "input_schema": {"type": "object", "properties": props, "required": required}}


S = {"type": "string"}
TOOL_SCHEMAS = [
    _schema("calculator", "Evaluate a math expression, e.g. '(12*7)/3'.",
            {"expression": S}, ["expression"]),
    _schema("wikipedia_search", "Look up a topic on Wikipedia and return a summary.",
            {"query": S}, ["query"]),
    _schema("save_note", "Save text to a markdown note file.",
            {"title": S, "content": S}, ["title", "content"]),
    _schema("read_note", "Read a previously saved note.", {"title": S}, ["title"]),
    _schema("list_notes", "List all saved notes.", {}, []),
    _schema("get_datetime", "Get the current date and time.", {}, []),
]

TOOL_FUNCS = {"calculator": calculator, "wikipedia_search": wikipedia_search,
              "save_note": save_note, "read_note": read_note,
              "list_notes": list_notes, "get_datetime": get_datetime}


def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_FUNCS:
        return f"Unknown tool: {name}"
    try:
        return str(TOOL_FUNCS[name](**args))
    except Exception as e:
        return f"Tool error: {e}"
