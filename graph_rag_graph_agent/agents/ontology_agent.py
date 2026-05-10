"""Ontology agent (v9): symbolic-reasoning RAG over an OWL ontology.

Symmetric to `RAGAgent`, `GraphAgent`, and `PageIndexAgent`: same
`BASE_PERSONA`, same scratchpad, same `ask` / `ask_with_trace` shape.
Three tools mirror Magaña Vsevolodovna & Monti (2025) §3 re-shaped as
a stand-alone retrieval interface:

- `get_ontology_summary()`  - TBox + sample ABox view (read once).
- `sparql_query(query)`     - native SPARQL via Owlready2.
- `check_consistency(claim)` - HermiT validation of a tentative claim.

Recursion cap is 24 (paradigm-symmetric to RAG and PageIndex; the
graph agent gets 40 because Cypher chains are typically deeper than
SPARQL queries on a small TBox).
"""

from __future__ import annotations

from collections import defaultdict
from contextvars import ContextVar
from typing import Any

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from graph_rag_graph_agent.agents.common import AgentRun, BASE_PERSONA, with_sections
from graph_rag_graph_agent.agents.memory import (
    SCRATCHPAD_TOOLS,
    set_active_thread,
)
from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.ontology.store import OntologyStore

# v9 introduces this paradigm. Few-shots use placeholders so we don't
# leak corpus-specific vocabulary into the prompt; the live TBox is
# provided to the agent on demand via `get_ontology_summary`,
# paradigm-symmetric to how `PageIndexAgent` gets the tree-of-contents
# and `GraphAgent` gets the Neo4j schema.
ONTOLOGY_SYSTEM_EXTRA = """\
Retrieval strategy:
- The corpus is indexed as an OWL 2 DL ontology. There is NO chunk
  retrieval, NO graph traversal, and NO tree-of-contents - you reason
  over the TBox (classes, properties, axioms) and ABox (individuals,
  assertions) using SPARQL plus a HermiT consistency-check tool.
- HermiT has already classified the TBox at build time, so subsumption
  and disjointness inferences are baked into what `get_ontology_summary`
  returns. You can rely on the inferred class hierarchy.

Tool order (do this on every question unless you've already cached
the summary for this thread):

  1. `get_ontology_summary()` - returns the class hierarchy, object-
     property list with domains/ranges, sample individuals per class,
     and any disjointness axioms. Read this once per session.
  2. `sparql_query(query)` - run one or more SPARQL queries against
     the loaded ontology. Use the prefixes the summary surfaces.
  3. `check_consistency(claim)` (optional) - submit a tentative
     assertion as `subject property object` triples; HermiT re-runs
     and tells you whether the claim is consistent with the TBox +
     existing ABox. Useful for negation / disjointness questions.
  4. Synthesise the answer from the SPARQL rows and (where used) the
     consistency verdict.

Search strategy by question shape:

Q: What is X / what does X do? (factual, single-property)
  -> get_ontology_summary(); SELECT for X's outgoing properties via
     SPARQL.

Q: Which entities depend on / relate to X (multi-hop)?
  -> SPARQL property paths: `?s :prop+ <X>` for the transitive case,
     `?s :prop ?mid . ?mid :prop2 <X>` for fixed-shape joins.

Q: Which entities are connected to BOTH X and Y (shared neighbour)?
  -> SPARQL with two triple patterns and a shared variable.

Q: Which entities do NOT have property/relation R?
  -> SPARQL `FILTER NOT EXISTS { ... }`. For tighter checks of a
     specific exclusion ("X is not a Y"), prefer `check_consistency`
     with the negated claim - HermiT will surface the disjointness
     axiom that rules it out, which is more reliable than a vocab-
     sensitive FILTER NOT EXISTS.

Q: How many entities have property P?
  -> SPARQL `SELECT (COUNT(?s) AS ?n) ...`. Always also list the
     names with a second `SELECT ?s WHERE { ... }` so the answer
     covers count + enumeration (the answer-shape contract).

SPARQL notes for this ontology:
- The ontology base IRI is surfaced in `get_ontology_summary`. Owlready2
  accepts queries with no PREFIX block by treating short names as
  ontology-local; you can also write `<#ClassName>` / `<#prop>` for
  explicit references.
- Class and property names are PascalCase and camelCase respectively.
  Individual names use the corpus's own spelling (often slug-like,
  e.g. `Auth_Service` for "Auth Service").
- The native engine supports SELECT, ASK, INSERT, DELETE, property
  paths, FILTER, and aggregations. Avoid CONSTRUCT in this paradigm
  (the agent's `check_consistency` tool serves the same purpose with
  cleaner semantics).

Notes on cost and budget:

- Cap on `check_consistency`: 3 calls per question. Reach for it on
  negation / disjointness checks, not on routine SPARQL retrieval.
- Stash candidate individual names in the scratchpad if you intend
  to issue several SPARQL queries on the same set.
- When a SPARQL result set is large, SUMMARISE rather than dumping
  every row.

When you've gathered enough, give a concise natural-language answer
and briefly cite which SPARQL pattern (or consistency check) supplied
the fact.
"""

# Code-enforced cap on `check_consistency` per question/thread,
# paradigm-symmetric to v6's `set_difference` cap and v4's `reach`
# cap. The cap fires on the (N+1)th call and returns an error
# steering the agent toward `sparql_query` instead.
CHECK_CONSISTENCY_CAP = 3

_check_consistency_calls: dict[str, int] = defaultdict(int)
_active_consistency_thread: ContextVar[str] = ContextVar(
    "consistency_thread", default="default"
)


def reset_consistency_state(thread_id: str) -> None:
    """Drop any cached `check_consistency` call counts for a thread."""
    _check_consistency_calls.pop(thread_id, None)


def _build_tools(store: OntologyStore) -> list[Any]:
    @tool
    def get_ontology_summary() -> str:
        """Return the TBox view: class hierarchy, properties, sample individuals.

        Read this once per session. Output covers:
        - Classes with their HermiT-classified parents.
        - Object properties with declared domain -> range.
        - Data properties with their range type.
        - Per-class individual counts and a small sample of names so
          you learn the corpus's spelling without us dumping every
          individual.
        - Disjointness pairs and any HermiT-flagged inconsistent
          classes.
        """
        return store.render_summary()

    @tool
    def sparql_query(query: str) -> str:
        """Run a SPARQL query against the loaded ontology.

        Args:
            query: a SPARQL 1.1 query string. SELECT, ASK, INSERT,
                DELETE, property paths, FILTER, and aggregations are
                supported (Owlready2's native engine). Owlready2
                resolves bare names as ontology-local; you may also
                write `<#ClassName>` / `<#propName>` for explicit
                fragment-IRI references.

        Returns:
            Pipe-delimited rows ending with a `(N rows)` footer, or
            `ERROR: ...` if the query fails to parse / execute.
        """
        return store.run_sparql(query)

    @tool
    def check_consistency(claim: str) -> str:
        """HermiT-validate a tentative claim against the loaded ontology.

        Args:
            claim: one or more lines, each `subject property object`
                separated by whitespace. Object may be a quoted
                literal (data property) or another individual name
                (object property). Lines starting with `#` are ignored.

        Behaviour:
            Asserts each triple into a temporary sub-ontology, re-runs
            HermiT, and returns `consistent: True/False`. If False,
            surfaces the conflicting axiom(s). The temporary triples
            are dropped before the call returns; this tool never
            mutates the persisted ontology.

        Use for negation / disjointness questions where a SPARQL
        `FILTER NOT EXISTS` would depend on vocabulary completeness.
        Cap of 3 calls per question/thread.
        """
        thread_id = _active_consistency_thread.get()
        count = _check_consistency_calls[thread_id]
        if count >= CHECK_CONSISTENCY_CAP:
            return (
                f"ERROR: check_consistency cap reached "
                f"({CHECK_CONSISTENCY_CAP} calls). Switch to "
                f"`sparql_query` to express the constraint as a "
                f"FILTER NOT EXISTS / ASK pattern, or finalise the "
                f"answer using what you have so far."
            )
        _check_consistency_calls[thread_id] = count + 1
        return store.check_consistency(claim)

    return [get_ontology_summary, sparql_query, check_consistency, *SCRATCHPAD_TOOLS]


class OntologyAgent:
    """LangGraph React agent that answers via SPARQL + HermiT over an OWL ontology."""

    def __init__(
        self,
        config: Config | None = None,
        store: OntologyStore | None = None,
    ) -> None:
        self.config = config or load_config()
        self.store = store or OntologyStore.load()
        self.llm = ChatOpenAI(
            model=self.config.openai.agent_model,
            api_key=self.config.openai.api_key,
            temperature=0,
        )
        self.checkpointer = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=_build_tools(self.store),
            prompt=with_sections(BASE_PERSONA, ONTOLOGY_SYSTEM_EXTRA),
            checkpointer=self.checkpointer,
        )

    def ask(self, question: str, thread_id: str = "default") -> str:
        return self.ask_with_trace(question, thread_id=thread_id).answer

    def ask_with_trace(self, question: str, thread_id: str = "default") -> AgentRun:
        """Run the agent and return both the final answer and the raw message list.

        Symmetric to the other four agents. The eval runner consumes the
        raw messages via `eval.trace.extract_trace` to compute tool-call
        counts and the v9 per-paradigm adoption counters
        (`ontology_consistency_calls`, `ontology_sparql_calls`).
        """
        set_active_thread(thread_id)
        _active_consistency_thread.set(thread_id)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 24,
            },
        )
        messages = result["messages"]
        answer = ""
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "ai" and getattr(msg, "content", None):
                answer = msg.content if isinstance(msg.content, str) else str(msg.content)
                break
        return AgentRun(answer=answer, messages=list(messages))
