"""Run both agents over the evaluation question set and score with the judge."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from graph_rag_graph_agent.agents.memory import reset_scratchpad
from graph_rag_graph_agent.agents.graph_agent import GraphAgent
from graph_rag_graph_agent.agents.rag_agent import RAGAgent
from graph_rag_graph_agent.config import (
    EVAL_RUNS_DIR,
    Config,
    load_config,
)
from graph_rag_graph_agent.eval.generate import QAPair, load_questions
from graph_rag_graph_agent.eval.judge import Judge, Judgement

console = Console()

AgentName = Literal["rag", "graph"]


@dataclass
class TurnResult:
    question_id: str
    category: str
    question: str
    expected_answer: str
    expected_entities: list[str]
    agent: AgentName
    agent_answer: str
    verdict: str
    rationale: str
    latency_seconds: float
    error: str | None = None


@dataclass
class RunSummary:
    run_id: str
    started_at: str
    agents: list[str]
    question_count: int
    results: list[TurnResult]
    output_path: str


def _verdict_score(verdict: str) -> float:
    return {"correct": 1.0, "partial": 0.5, "wrong": 0.0}.get(verdict, 0.0)


def run_eval(
    agents: list[AgentName] | None = None,
    questions: list[QAPair] | None = None,
    config: Config | None = None,
) -> RunSummary:
    config = config or load_config()
    agents = agents or ["rag", "graph"]
    questions = questions or load_questions()

    console.print(
        f"[bold]Running eval[/bold] "
        f"({len(questions)} questions x {len(agents)} agents)"
    )

    runners: dict[AgentName, RAGAgent | GraphAgent] = {}
    if "rag" in agents:
        runners["rag"] = RAGAgent(config)
    if "graph" in agents:
        runners["graph"] = GraphAgent(config)

    judge = Judge(config)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    results: list[TurnResult] = []

    for q in tqdm(questions, desc="questions"):
        for agent_name in agents:
            thread_id = f"{run_id}-{agent_name}-{q.id}"
            reset_scratchpad(thread_id)
            runner = runners[agent_name]
            start = time.perf_counter()
            error: str | None = None
            try:
                answer = runner.ask(q.question, thread_id=thread_id)
            except Exception as exc:  # noqa: BLE001
                answer = f"(agent error: {type(exc).__name__}: {exc})"
                error = str(exc)
            latency = time.perf_counter() - start

            judgement: Judgement
            try:
                judgement = judge.score(
                    question=q.question,
                    expected_answer=q.expected_answer,
                    expected_entities=q.expected_entities,
                    agent_answer=answer,
                )
            except Exception as exc:  # noqa: BLE001
                judgement = Judgement(verdict="wrong", rationale=f"judge error: {exc}", raw="")

            results.append(
                TurnResult(
                    question_id=q.id,
                    category=q.category,
                    question=q.question,
                    expected_answer=q.expected_answer,
                    expected_entities=q.expected_entities,
                    agent=agent_name,
                    agent_answer=answer,
                    verdict=judgement.verdict,
                    rationale=judgement.rationale,
                    latency_seconds=latency,
                    error=error,
                )
            )

    EVAL_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EVAL_RUNS_DIR / f"{run_id}.json"
    summary = RunSummary(
        run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
        agents=list(agents),
        question_count=len(questions),
        results=results,
        output_path=str(out_path),
    )
    out_path.write_text(
        json.dumps({**asdict(summary), "results": [asdict(r) for r in results]}, indent=2),
        encoding="utf-8",
    )
    console.print(f"[green]Raw run saved to {out_path}[/green]")
    _print_quick_summary(results, agents)
    return summary


def _print_quick_summary(results: list[TurnResult], agents: list[AgentName]) -> None:
    table = Table(title="Quick summary (score = correct=1, partial=0.5, wrong=0)")
    table.add_column("Category", style="bold")
    for a in agents:
        table.add_column(a)

    categories = sorted({r.category for r in results})
    per_cat: dict[str, dict[str, list[float]]] = {
        c: {a: [] for a in agents} for c in categories
    }
    for r in results:
        per_cat[r.category][r.agent].append(_verdict_score(r.verdict))

    for cat in categories:
        row = [cat]
        for a in agents:
            scores = per_cat[cat][a]
            if scores:
                row.append(f"{sum(scores) / len(scores):.2f}  ({len(scores)})")
            else:
                row.append("-")
        table.add_row(*row)

    overall = ["overall"]
    for a in agents:
        all_scores = [_verdict_score(r.verdict) for r in results if r.agent == a]
        if all_scores:
            overall.append(f"{sum(all_scores) / len(all_scores):.2f}  ({len(all_scores)})")
        else:
            overall.append("-")
    table.add_row(*overall, style="bold")

    console.print(table)
