"""CLI: python main.py "your task"   or   python main.py  (interactive)"""
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.core import ResearchAgent  # noqa: E402


def main():
    agent = ResearchAgent()
    if len(sys.argv) > 1:
        print("\n=== FINAL ANSWER ===\n" + agent.run(" ".join(sys.argv[1:])))
        return
    print("Agentic Research Agent. Type 'exit' to quit.")
    while True:
        task = input("\nTask> ").strip()
        if task.lower() in {"exit", "quit"}:
            break
        if task:
            print("\n=== FINAL ANSWER ===\n" + agent.run(task))


if __name__ == "__main__":
    main()
