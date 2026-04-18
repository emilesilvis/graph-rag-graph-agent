"""Shared scratchpad tool factory.

Both agents get a small key/value scratchpad they can write to across turns
within the same conversation (thread). Useful for multi-hop questions: the
agent can jot down intermediate findings (entity IDs, partial results, etc.)
and retrieve them later in the same session.

The store is keyed by `thread_id` so sessions are isolated.
"""

from __future__ import annotations

from collections import defaultdict
from contextvars import ContextVar

from langchain_core.tools import tool

_SCRATCHPADS: dict[str, dict[str, str]] = defaultdict(dict)

_current_thread: ContextVar[str] = ContextVar("scratchpad_thread", default="default")


def set_active_thread(thread_id: str) -> None:
    """Set which thread's scratchpad the scratchpad tools will target."""
    _current_thread.set(thread_id)


def _pad() -> dict[str, str]:
    return _SCRATCHPADS[_current_thread.get()]


@tool
def scratchpad_write(key: str, value: str) -> str:
    """Save a short note under `key` so you can recall it later in this session.

    Use this to stash intermediate findings while you work through a question
    (for example, the set of services you've found so far). Overwrites any
    existing note at that key.
    """
    _pad()[key] = value
    return f"Saved note under key '{key}' ({len(value)} chars)."


@tool
def scratchpad_read(key: str = "") -> str:
    """Read a saved note by `key`, or pass an empty key to list all saved keys."""
    pad = _pad()
    if not key:
        if not pad:
            return "Scratchpad is empty."
        return "Saved keys: " + ", ".join(sorted(pad.keys()))
    if key not in pad:
        return f"No note saved under '{key}'. Saved keys: {sorted(pad.keys())}"
    return pad[key]


@tool
def scratchpad_clear() -> str:
    """Erase all saved notes for this session."""
    pad = _pad()
    count = len(pad)
    pad.clear()
    return f"Cleared {count} saved notes."


SCRATCHPAD_TOOLS = [scratchpad_write, scratchpad_read, scratchpad_clear]


def reset_scratchpad(thread_id: str) -> None:
    """Drop any stored notes for the given thread (used between eval runs)."""
    _SCRATCHPADS.pop(thread_id, None)
