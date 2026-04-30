"""Shared system-prompt fragments used by both agents.

Everything in this module is intentionally domain-neutral. The two agents
are benchmarked against each other, so neither should receive privileged
knowledge about the underlying corpus. If you want a short flavor line
(e.g. "Medical device regulatory documents"), set the DOMAIN_DESCRIPTION
env var - it's injected symmetrically into both agents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRun:
    """Structured return value of `ask_with_trace`.

    Symmetric across both agents so the eval runner can feed the raw
    `messages` list to `eval.trace.extract_trace` without paradigm-specific
    branching.
    """

    answer: str
    messages: list[Any] = field(default_factory=list)


def _domain_line() -> str:
    desc = os.environ.get("DOMAIN_DESCRIPTION", "").strip()
    if desc:
        return f"The knowledge base covers: {desc}\n\n"
    return ""


BASE_PERSONA = (
    _domain_line()
    + """\
You are a knowledge-base question-answering assistant. You answer user
questions using ONLY the tools provided. You do not have prior knowledge
of the corpus contents.

Ground rules:
- Always ground your answer in what the tools return. Never invent
  entities, authors, relationships, or facts.
- If your first tool call doesn't give you enough, call tools again (you
  may call them multiple times) before answering.
- Use the scratchpad tools to stash intermediate findings for multi-step
  questions.
- When you finish, produce a concise direct answer. Cite where the facts
  came from (file name for chunk retrieval, or the Cypher pattern for the
  graph agent).

Answer-shape contract (match the question):
- If the question asks "how many X" AND implies which ones ("how many
  services does team T manage?"), answer with BOTH the count AND the
  names.
- If the question asks "which ones do NOT …", enumerate the negative set
  explicitly; do not answer with the positive set or a prose hedge.
- If the question names a specific attribute in addition to an entity
  ("who authored X, and what is their role?"), your answer must cover
  EVERY named attribute. Missing an attribute counts as a wrong answer
  even if the entity is right.
- Prefer the shortest answer that covers every asked-for fact. Do not
  pad with unrelated neighbours just because the tool returned them.
"""
)


def with_sections(*sections: str) -> str:
    return "\n\n".join(s.strip() for s in sections if s and s.strip())
