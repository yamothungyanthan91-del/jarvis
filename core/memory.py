"""
Simple persistent memory.
Jarvis remembers facts you tell it to remember (e.g. family members,
preferences) in a local file called memory.json, which stays only on
your device (it's git-ignored, never uploaded to GitHub).
"""
import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.json")


def load_facts() -> list[str]:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_fact(fact: str) -> None:
    facts = load_facts()
    facts.append(fact.strip())
    with open(MEMORY_FILE, "w") as f:
        json.dump(facts, f, indent=2)


def facts_as_text() -> str:
    facts = load_facts()
    if not facts:
        return "No personal facts stored yet."
    return "\n".join(f"- {f}" for f in facts)
