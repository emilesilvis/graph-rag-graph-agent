"""Run both agents over the evaluation question set and score with the judge."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from graph_rag_graph_agent.agents.memory import reset_scratchpad
from graph_rag_graph_agent.agents.graph_agent import GraphAgent
from graph_rag_graph_agent.agents.pageindex_agent import PageIndexAgent
from graph_rag_graph_agent.agents.rag_agent import RAGAgent
from graph_rag_graph_agent.agents.router_agent import RouterAgent
from graph_rag_graph_agent.graph.tools import reset_reach_state
from graph_rag_graph_agent.config import (
    EVAL_RUNS_DIR,
    Config,
    load_config,
)
from graph_rag_graph_agent.eval.generate import QAPair, load_questions
from graph_rag_graph_agent.eval.judge import Judge, Judgement
from graph_rag_graph_agent.eval.oracle import (
    OracleResult,
    attribute_status,
    run_oracle,
)
from graph_rag_graph_agent.eval.trace import (
    AgentTraceSummary,
    extract_trace,
    trace_to_dict,
)

console = Console()

AgentName = Literal["rag", "graph", "pageindex", "router"]


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
    # v3 instrumentation. None / empty defaults so old reports keep loading.
    concepts_in_question: list[str] = field(default_factory=list)
    oracle_cypher: str = ""
    oracle_row_count: int = 0
    oracle_has_oracle: bool = False
    oracle_error: str | None = None
    oracle_status: str = "no_oracle"
    oracle_enumeration: list[str] | None = None
    tool_call_count: int = 0
    hit_recursion_limit: bool = False
    step_at_first_relevant_match: int | None = None
    find_rel_types_like_calls: dict[str, bool] = field(default_factory=dict)
    aliases_used_calls: int = 0
    set_difference_calls: int = 0
    pageindex_section_calls: int = 0
    router_calls: dict[str, int] = field(default_factory=dict)
    router_primary: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)


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

    runners: dict[AgentName, RAGAgent | GraphAgent | PageIndexAgent | RouterAgent] = {}
    if "rag" in agents:
        runners["rag"] = RAGAgent(config)
    if "graph" in agents:
        runners["graph"] = GraphAgent(config)
    if "pageindex" in agents:
        runners["pageindex"] = PageIndexAgent(config)
    if "router" in agents:
        # Router needs all three sub-agents. Reuse already-built ones if
        # present so we don't double-pay the (cheap but non-zero) init
        # cost; build any missing ones here.
        rag_sub = runners.get("rag") if isinstance(runners.get("rag"), RAGAgent) else None
        graph_sub = (
            runners.get("graph") if isinstance(runners.get("graph"), GraphAgent) else None
        )
        pi_sub = (
            runners.get("pageindex")
            if isinstance(runners.get("pageindex"), PageIndexAgent)
            else None
        )
        runners["router"] = RouterAgent(
            config=config,
            rag=rag_sub or RAGAgent(config),
            graph=graph_sub or GraphAgent(config),
            pageindex=pi_sub or PageIndexAgent(config),
        )

    judge = Judge(config)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    results: list[TurnResult] = []

    # Cache oracle execution per question (independent of agent).
    oracle_cache: dict[str, OracleResult] = {}

    for q in tqdm(questions, desc="questions"):
        if q.id not in oracle_cache:
            try:
                oracle_cache[q.id] = run_oracle(q.seed_cypher, config=config)
            except Exception as exc:  # noqa: BLE001 - never let oracle break eval
                oracle_cache[q.id] = OracleResult(
                    cypher=q.seed_cypher,
                    row_count=0,
                    error=f"{type(exc).__name__}: {exc}",
                    has_oracle=bool(q.seed_cypher and q.seed_cypher.strip()),
                )
        oracle = oracle_cache[q.id]

        for agent_name in agents:
            thread_id = f"{run_id}-{agent_name}-{q.id}"
            reset_scratchpad(thread_id)
            reset_reach_state(thread_id)
            runner = runners[agent_name]
            start = time.perf_counter()
            error: str | None = None
            messages: list[Any] = []
            try:
                run = runner.ask_with_trace(q.question, thread_id=thread_id)
                answer = run.answer
                messages = run.messages
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

            trace: AgentTraceSummary = extract_trace(
                messages,
                expected_entities=q.expected_entities,
                concepts_in_question=q.concepts_in_question,
            )
            oracle_status = attribute_status(
                agent_name=agent_name,
                verdict=judgement.verdict,
                oracle=oracle,
            )

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
                    concepts_in_question=list(q.concepts_in_question),
                    oracle_cypher=oracle.cypher,
                    oracle_row_count=oracle.row_count,
                    oracle_has_oracle=oracle.has_oracle,
                    oracle_error=oracle.error,
                    oracle_status=oracle_status,
                    oracle_enumeration=(
                        list(oracle.enumeration)
                        if oracle.enumeration is not None
                        else None
                    ),
                    tool_call_count=trace.tool_call_count,
                    hit_recursion_limit=trace.hit_recursion_limit,
                    step_at_first_relevant_match=trace.step_at_first_relevant_match,
                    find_rel_types_like_calls=dict(trace.find_rel_types_like_calls),
                    aliases_used_calls=trace.aliases_used_calls,
                    set_difference_calls=trace.set_difference_calls,
                    pageindex_section_calls=trace.pageindex_section_calls,
                    router_calls=dict(trace.router_calls),
                    router_primary=trace.router_primary,
                    trace=trace_to_dict(trace),
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
