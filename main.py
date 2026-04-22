"""CLI entry point for the two-agent RAG project.

Every subcommand is intended to be invoked via `uv run`, e.g.

    uv run python main.py ingest-rag
    uv run python main.py load-graph
    uv run python main.py generate-eval --n 25
    uv run python main.py eval
    uv run python main.py chat --agent graph
    uv run python main.py new-iteration --id v2 --run-id <run_id>
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(add_completion=False, help="Chunk-RAG vs Graph-RAG agent harness.")
console = Console()


@app.command("ingest-rag")
def ingest_rag(
    rebuild: bool = typer.Option(
        True,
        "--rebuild/--no-rebuild",
        help="If true (default), wipe and rebuild the Chroma index.",
    ),
) -> None:
    """(Re)build the Chroma vector index from knowledge_sources/*.md."""
    from graph_rag_graph_agent.rag.ingest import build_index

    build_index(rebuild=rebuild)


@app.command("load-graph")
def load_graph(
    reset: bool = typer.Option(
        True,
        "--reset/--no-reset",
        help="If true (default), wipe the graph before loading.",
    ),
) -> None:
    """Load knowledge_sources/graph.cypher into Neo4j."""
    from graph_rag_graph_agent.graph.loader import load_graph as _load

    _load(reset=reset)


@app.command("generate-eval")
def generate_eval(
    n: int = typer.Option(25, "--n", help="Approximate total number of questions."),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for sampling."),
) -> None:
    """Sample the graph and synthesize categorized Q&A pairs into eval/questions.yaml."""
    from graph_rag_graph_agent.eval.generate import generate_questions

    generate_questions(total=n, seed=seed)


@app.command("eval")
def eval_cmd(
    agent: str = typer.Option(
        "both",
        "--agent",
        help="Which agent(s) to run: rag | graph | both.",
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Optional cap on number of questions to run (debug)."
    ),
    questions_path: Optional[Path] = typer.Option(
        None,
        "--questions",
        "-q",
        help="Path to a questions YAML. Defaults to the auto-generated eval set.",
    ),
) -> None:
    """Run the eval set through the selected agents and produce a markdown report."""
    from graph_rag_graph_agent.eval.generate import load_questions
    from graph_rag_graph_agent.eval.report import write_report
    from graph_rag_graph_agent.eval.run import run_eval

    agent_choice = agent.lower().strip()
    if agent_choice == "both":
        agents = ["rag", "graph"]
    elif agent_choice in {"rag", "graph"}:
        agents = [agent_choice]  # type: ignore[list-item]
    else:
        raise typer.BadParameter("--agent must be one of rag | graph | both")

    questions = load_questions(questions_path)
    if limit is not None:
        questions = questions[:limit]

    summary = run_eval(agents=agents, questions=questions)
    report_path = write_report()
    console.print(f"[green]Report written to {report_path}[/green]")
    typer.echo(f"Raw results: {summary.output_path}")


@app.command("chat")
def chat(
    agent: str = typer.Option(
        "rag", "--agent", help="Which agent to chat with: rag | graph."
    ),
) -> None:
    """Interactive REPL against one of the agents (same thread, memory persists)."""
    agent_choice = agent.lower().strip()
    if agent_choice == "rag":
        from graph_rag_graph_agent.agents.rag_agent import RAGAgent

        runner = RAGAgent()
        label = "RAG agent"
    elif agent_choice == "graph":
        from graph_rag_graph_agent.agents.graph_agent import GraphAgent

        runner = GraphAgent()
        label = "Graph agent"
    else:
        raise typer.BadParameter("--agent must be rag | graph")

    thread_id = "chat-session"
    console.print(
        Panel.fit(
            f"[bold]{label}[/bold]\nType a question (Ctrl-C or empty line to quit).",
            border_style="cyan",
        )
    )
    while True:
        try:
            question = typer.prompt("you", default="", show_default=False)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]bye.[/dim]")
            break
        if not question.strip():
            break
        answer = runner.ask(question, thread_id=thread_id)
        console.print(Panel(answer or "(empty)", title=label, border_style="green"))


def _yaml_quote(value: str) -> str:
    """Quote a string for safe emission as a single-line YAML value."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_iteration_yaml(
    iter_id: str,
    created_at: str,
    parent: Optional[str],
    run_id: str,
    agents: list[str],
    question_count: int,
    summary: str,
    changes: list[str],
) -> str:
    parent_line = parent if parent else "null"
    lines = [
        f"id: {iter_id}",
        f"created_at: {created_at}",
        f"parent: {parent_line}",
        f"run_id: {run_id}",
        "agents:",
    ]
    for a in agents:
        lines.append(f"  - {a}")
    lines.append(f"question_count: {question_count}")
    if summary:
        lines.append(f"summary: {_yaml_quote(summary)}")
    else:
        lines.append('summary: ""')
    if changes:
        lines.append("changes:")
        for c in changes:
            lines.append(f"  - {_yaml_quote(c)}")
    else:
        lines.append("changes: []")
    return "\n".join(lines) + "\n"


@app.command("new-iteration")
def new_iteration(
    iter_id: str = typer.Option(
        ..., "--id", help="Iteration id, e.g. v2. Must not already exist."
    ),
    run_id: str = typer.Option(
        ..., "--run-id", help="Eval run id to freeze into this iteration."
    ),
    parent: Optional[str] = typer.Option(
        None,
        "--parent",
        help="Previous iteration id (e.g. v1). Defaults to the current "
        "`iterations/latest` symlink if one exists.",
    ),
    summary: str = typer.Option(
        "", "--summary", help="Short free-text summary of changes in this iteration."
    ),
    change: list[str] = typer.Option(
        [],
        "--change",
        help="One changelog bullet. Pass multiple times for multiple bullets.",
    ),
    from_paper: Optional[Path] = typer.Option(
        None,
        "--from-paper",
        help="Path to a paper.md to snapshot. Defaults to the parent "
        "iteration's paper.md, or repo-root paper.md if no parent.",
    ),
) -> None:
    """Freeze an eval run + paper.md into iterations/<id>/.

    This is the only supported way to promote scratch eval output into Git.
    Behaviour (see plan file for full policy):
      1. Create iterations/<id>/ (refuses if it exists).
      2. Copy eval_runs/<run_id>.json into iterations/<id>/eval_run.json.
      3. Render eval_report.md for that run into iterations/<id>/.
      4. Copy the chosen paper.md into iterations/<id>/.
      5. Write iteration.yaml metadata.
      6. Update iterations/latest symlink.
      7. Copy iterations/<id>/paper.md back to repo-root paper.md.
    """
    from graph_rag_graph_agent.config import EVAL_RUNS_DIR, PROJECT_ROOT
    from graph_rag_graph_agent.eval.report import write_report

    iterations_dir = PROJECT_ROOT / "iterations"
    target_dir = iterations_dir / iter_id
    if target_dir.exists():
        raise typer.BadParameter(
            f"iterations/{iter_id}/ already exists; refusing to overwrite."
        )

    run_path = EVAL_RUNS_DIR / f"{run_id}.json"
    if not run_path.exists():
        raise typer.BadParameter(
            f"eval_runs/{run_id}.json does not exist. Run the eval first "
            f"or pick a different --run-id."
        )

    if parent is None:
        latest = iterations_dir / "latest"
        if latest.exists():
            parent = latest.resolve().name

    if from_paper is None:
        if parent is not None:
            candidate = iterations_dir / parent / "paper.md"
            if candidate.exists():
                from_paper = candidate
        if from_paper is None:
            from_paper = PROJECT_ROOT / "paper.md"
    from_paper = from_paper.resolve()
    if not from_paper.exists():
        raise typer.BadParameter(f"Source paper not found: {from_paper}")

    target_dir.mkdir(parents=True)
    shutil.copy2(run_path, target_dir / "eval_run.json")
    write_report(run_path=run_path, out_path=target_dir / "eval_report.md")
    shutil.copy2(from_paper, target_dir / "paper.md")

    data = json.loads(run_path.read_text(encoding="utf-8"))
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    yaml_text = _render_iteration_yaml(
        iter_id=iter_id,
        created_at=created_at,
        parent=parent,
        run_id=run_id,
        agents=list(data.get("agents", [])),
        question_count=int(data.get("question_count", 0)),
        summary=summary,
        changes=list(change),
    )
    (target_dir / "iteration.yaml").write_text(yaml_text, encoding="utf-8")

    latest_link = iterations_dir / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(iter_id, target_is_directory=True)

    shutil.copy2(target_dir / "paper.md", PROJECT_ROOT / "paper.md")

    console.print(
        f"[green]Cut iteration {iter_id}[/green] "
        f"(run {run_id}, parent={parent or 'null'}).\n"
        f"  iterations/{iter_id}/\n"
        f"  iterations/latest -> {iter_id}\n"
        f"  paper.md (root) refreshed."
    )


if __name__ == "__main__":
    app()
