"""Run a gold question's seed Cypher against the live graph for attribution.

The gold YAML carries a `seed_cypher` per question that, when executed
against the extracted graph, returns the rows the gold answer is grounded
in. We use it as an oracle: the row count produced by the live graph tells
us whether the answer is reachable from the graph at all.

This lets us split graph-agent failures into:
  - extraction_miss : oracle returned 0 rows / no oracle. The graph itself
                      does not support the answer; no agent change can fix
                      this without re-extracting.
  - agent_miss      : oracle returned >=1 rows AND the agent answered wrong
                      or partial. The information was reachable; this is a
                      reasoning failure, attributable to the agent.
  - agent_ok        : oracle returned >=1 rows AND the agent answered
                      correctly.
  - no_oracle       : the gold question has no seed_cypher (rare; e.g.
                      `gold-002` where the fact lives only in markdown).

For the RAG agent, `extraction_miss` does not apply (chunk retrieval does
not depend on the graph extraction). The reporter labels RAG rows as
`agent_ok` / `agent_miss` based on verdict alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver


@dataclass
class OracleResult:
    cypher: str
    row_count: int
    error: str | None
    has_oracle: bool


def run_oracle(cypher: str, config: Config | None = None) -> OracleResult:
    """Execute `cypher` read-only and return how many rows it produced.

    Empty / whitespace-only `cypher` is treated as "no oracle". Errors are
    captured but do not raise.
    """
    if not cypher or not cypher.strip():
        return OracleResult(cypher="", row_count=0, error=None, has_oracle=False)

    config = config or load_config()
    driver = get_driver(config)
    try:
        with driver.session() as session:
            result = session.run(cypher)
            rows = list(result)
    except Exception as exc:  # noqa: BLE001 - surface DB error in result
        return OracleResult(
            cypher=cypher,
            row_count=0,
            error=f"{type(exc).__name__}: {exc}",
            has_oracle=True,
        )
    return OracleResult(
        cypher=cypher,
        row_count=len(rows),
        error=None,
        has_oracle=True,
    )


def attribute_status(
    *,
    agent_name: str,
    verdict: str,
    oracle: OracleResult,
) -> str:
    """Return one of: agent_ok, agent_miss, extraction_miss, no_oracle.

    Semantics:
    - For graph-agent rows: empty `seed_cypher` (no oracle) AND oracle
      returning 0 rows are both treated as `extraction_miss`. The gold
      author's intent for an empty seed is "this fact lives only in
      markdown", which is exactly an extraction miss for the graph
      paradigm.
    - For RAG rows: the oracle does not constrain the answer space (RAG
      retrieves from markdown, not from the graph), so attribution is
      purely verdict-based and `no_oracle` rows contribute to `agent_ok`
      / `agent_miss`.
    """
    if agent_name == "graph":
        # A seed Cypher that fails to execute is a gold-YAML bug, not an
        # extraction miss; surface it as `no_oracle` so it is clearly
        # broken-out from genuine extraction-bound rows.
        if oracle.has_oracle and oracle.error:
            return "no_oracle"
        if not oracle.has_oracle or oracle.row_count == 0:
            return "extraction_miss"
        return "agent_ok" if verdict == "correct" else "agent_miss"
    # RAG (or any non-graph paradigm): verdict-only.
    return "agent_ok" if verdict == "correct" else "agent_miss"
