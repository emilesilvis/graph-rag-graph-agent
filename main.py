"""CLI entry point for the two-agent RAG project.

Every subcommand is intended to be invoked via `uv run`, e.g.

    uv run python main.py ingest-rag
    uv run python main.py load-graph
    uv run python main.py generate-eval --n 25
    uv run python main.py eval
    uv run python main.py chat --agent graph
"""

from __future__ import annotations

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


if __name__ == "__main__":
    app()
