"""Load `knowledge_sources/graph.cypher` into Neo4j.

The file contains one `MERGE ... MERGE ... CREATE` statement per line, so the
loader just splits on `;`, skips blanks, and executes in batches inside a
single session. Because the statements use `MERGE` for nodes, re-running is
safe; the `CREATE` of the relationship will duplicate edges between the same
pair unless we first wipe the graph - we therefore offer a `--reset` option
(on by default in the CLI) that deletes existing data before loading.
"""

from __future__ import annotations

from pathlib import Path

from neo4j import Driver
from rich.console import Console
from tqdm import tqdm

from graph_rag_graph_agent.config import GRAPH_CYPHER_PATH, Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver

console = Console()


def _read_statements(cypher_path: Path) -> list[str]:
    text = cypher_path.read_text(encoding="utf-8")
    parts = [p.strip() for p in text.split(";")]
    return [p for p in parts if p]


def _wipe_graph(driver: Driver) -> None:
    console.print("[yellow]Wiping existing graph (MATCH (n) DETACH DELETE n)...[/yellow]")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n").consume()


def _ensure_indexes(driver: Driver) -> None:
    with driver.session() as session:
        session.run(
            "CREATE INDEX entity_name_index IF NOT EXISTS "
            "FOR (e:Entity) ON (e.name)"
        ).consume()


def load_graph(
    reset: bool = True,
    config: Config | None = None,
    cypher_path: Path | None = None,
) -> dict[str, int]:
    """Load the cypher file into Neo4j. Returns counts for nodes and rels."""
    config = config or load_config()
    cypher_path = cypher_path or GRAPH_CYPHER_PATH
    if not cypher_path.exists():
        raise RuntimeError(f"Cypher file not found: {cypher_path}")

    statements = _read_statements(cypher_path)
    console.print(f"[dim]Loaded {len(statements)} statements from {cypher_path.name}[/dim]")

    driver = get_driver(config)
    if reset:
        _wipe_graph(driver)
    _ensure_indexes(driver)

    with driver.session() as session:
        for stmt in tqdm(statements, desc="cypher"):
            session.run(stmt).consume()

    with driver.session() as session:
        node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

    console.print(
        f"[green]Graph loaded: {node_count} nodes, {rel_count} relationships.[/green]"
    )
    return {"nodes": node_count, "relationships": rel_count}
