import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent import tools  # noqa: E402


def test_calculator():
    assert tools.calculator("(12*7)/3") == "28.0"


def test_calculator_blocks_unsafe():
    assert tools.calculator("__import__('os').system('ls')").startswith("Error")


def test_notes_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "NOTES_DIR", str(tmp_path))
    tools.save_note("demo", "hello")
    assert tools.read_note("demo") == "hello"
    assert "demo.md" in tools.list_notes()


def test_unknown_tool():
    assert "Unknown" in tools.run_tool("nope", {})
