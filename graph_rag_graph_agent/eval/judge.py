"""LLM-as-judge scoring for agent answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from graph_rag_graph_agent.config import Config, load_config

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_SYSTEM = """\
You are a strict but fair grader. You score an agent's answer to an
evaluation question against a known-good expected answer / expected entities.

Return ONLY a JSON object with keys:
  verdict       : one of "correct", "partial", "wrong"
  rationale     : one short sentence (<= 25 words) explaining the verdict

Grading rules:
- "correct"  : the agent's answer states the same facts as the expected answer
  and mentions all expected entities (abbreviations and common synonyms are
  OK, e.g. "NYC" == "New York City").
- "partial"  : the answer mentions SOME of the expected entities or is on
  the right track but incomplete or hedges.
- "wrong"    : the answer is missing the key entities, contradicts the
  expected answer, says it doesn't know, or is clearly hallucinated.
- A refusal or "I don't have enough information" counts as "wrong".
"""


@dataclass
class Judgement:
    verdict: str
    rationale: str
    raw: str


class Judge:
    def __init__(self, config: Config | None = None) -> None:
        config = config or load_config()
        self.llm = ChatOpenAI(
            model=config.openai.judge_model,
            api_key=config.openai.api_key,
            temperature=0,
        )

    def score(
        self,
        question: str,
        expected_answer: str,
        expected_entities: list[str],
        agent_answer: str,
    ) -> Judgement:
        payload = {
            "question": question,
            "expected_answer": expected_answer,
            "expected_entities": expected_entities,
            "agent_answer": agent_answer,
        }
        resp = self.llm.invoke(
            [
                {"role": "system", "content": JUDGE_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        "Grade the following agent answer.\n\n"
                        + json.dumps(payload, indent=2)
                    ),
                },
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        verdict = "wrong"
        rationale = "(parse failure)"
        match = _JSON_RE.search(content)
        if match:
            try:
                parsed = json.loads(match.group(0))
                v = str(parsed.get("verdict", "")).lower().strip()
                if v in {"correct", "partial", "wrong"}:
                    verdict = v
                rationale = str(parsed.get("rationale", rationale)).strip()
            except json.JSONDecodeError:
                pass
        return Judgement(verdict=verdict, rationale=rationale, raw=content)
