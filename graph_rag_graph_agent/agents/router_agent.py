"""Router agent (v8): meta ReAct agent over the three paradigm sub-agents.

Wraps `RAGAgent`, `GraphAgent`, and `PageIndexAgent` behind three tools
(`ask_rag`, `ask_graph`, `ask_pageindex`). The router consults at least
one and may consult several, then synthesises a final answer. Routing
heuristics in the prompt are derived from the v7 paper's per-cell
findings (paper.md §3.1, §3.3) — not from corpus vocabulary, so they
remain domain-neutral and paradigm-symmetric.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from graph_rag_graph_agent.agents.common import AgentRun, BASE_PERSONA, with_sections
from graph_rag_graph_agent.agents.graph_agent import GraphAgent
from graph_rag_graph_agent.agents.memory import (
    SCRATCHPAD_TOOLS,
    reset_scratchpad,
    set_active_thread,
)
from graph_rag_graph_agent.agents.pageindex_agent import PageIndexAgent
from graph_rag_graph_agent.agents.rag_agent import RAGAgent
from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.tools import reset_reach_state

# v8 introduces this paradigm-routing variant. Few-shots stay placeholder-
# style ("a question of shape <X>") so the prompt doesn't leak corpus
# vocabulary, paradigm-symmetric to RAG / Graph / PageIndex prompts. The
# routing rules below are derived from the v7 paper §3.1/§3.3 per-cell
# table — multi_hop_2 cross-section joins go to graph (0.90 vs 0.20/0.00),
# one_hop and aggregation_count single-section answers go to pageindex
# (0.90, 0.62 vs the others), negation goes to rag or graph; the tied
# cells (multi_hop_3, dependency_chain, shared_neighbor) start at graph.
ROUTER_SYSTEM_EXTRA = """\
Routing strategy:
- You are the META agent. You do NOT retrieve the corpus directly. Your
  three retrieval tools each delegate the question to a different
  retrieval paradigm and return that paradigm's natural-language answer:
  - `ask_rag(question)`   — chunk-RAG over a Chroma vector index. Strong
                            on single-section semantic lookups and on
                            negation when the corpus uses consistent
                            vocabulary; weak on cross-section joins.
  - `ask_graph(question)` — graph-RAG over a Neo4j graph extracted
                            automatically from the markdown. Strong on
                            cross-section joins (entity-A is related to
                            entity-B is related to entity-C), shared-
                            neighbour, and dependency-chain queries.
                            Weak on facts the extractor missed.
  - `ask_pageindex(question)` — vectorless tree-of-contents reasoning
                            RAG. Strong on questions whose answer fits
                            inside one section ("how many X", "what is
                            X"), and on facts the graph extractor
                            dropped. Weak on cross-section joins where
                            it can run out of recursion budget.
- Pick ONE paradigm based on the question shape and call its tool. If
  the answer comes back convincing and complete, return it. If the
  paradigm hedges, contradicts itself, or hits its own step cap (the
  marker is "Sorry, need more steps to process this request"), call a
  SECOND paradigm and reconcile.
- You may call all three on hard questions, but prefer one if you can —
  each sub-agent call costs latency and budget.

Question-shape -> paradigm rules (start here, override only with reason):

| Question shape                              | First call    | Backup       |
| ------------------------------------------- | ------------- | ------------ |
| "What is X / what does X do?" (1-hop)       | pageindex     | rag          |
| "How many X have property P?" (count)       | pageindex     | graph        |
| "Which X depends-on / relates-to Y?"        | graph         | pageindex    |
| "Who authored / owns X, and their role?"    | graph         | pageindex    |
| (cross-section join, 2-hop)                 |               |              |
| "X about Y, and Z about X" (3-hop chain)    | graph         | pageindex    |
| "Which X's are connected to BOTH A and B?"  | graph         | pageindex    |
| (shared neighbour)                          |               |              |
| "Which X do NOT have property R?"           | graph         | rag          |
| (negation / set difference)                 |               |              |
| Anything else / unclear                     | graph         | pageindex    |

Answer-shape contract:
- After consulting one or more paradigms, return ONE concise final
  answer. Do not return three answers concatenated.
- Briefly mention which paradigm(s) you consulted and why. The fact
  that you picked, e.g. graph for a cross-section join, is part of the
  trace.
- If two paradigms disagree, prefer the one whose answer cites concrete
  evidence (the graph agent cites a Cypher pattern; the pageindex agent
  cites node_ids; the RAG agent cites file names). If both cite
  evidence, prefer the one whose evidence matches the question shape
  (cross-section join -> graph; single-section fact -> pageindex /
  rag).

Notes:
- Do NOT pass the question through tweaked or rephrased. Pass it
  verbatim to the sub-agent. The sub-agent has its own prompt for
  query reformulation.
- Each sub-agent is a fresh thread per question; you do not share
  memory with them.
- Use the scratchpad to record the paradigm you consulted and any
  intermediate findings if you intend to consult a second paradigm.
"""


def _build_tools(
    rag: RAGAgent,
    graph: GraphAgent,
    pageindex: PageIndexAgent,
    router_thread_id_holder: dict[str, str],
) -> list[Any]:
    def _sub_thread(paradigm: str) -> str:
        base = router_thread_id_holder.get("thread_id", "default")
        return f"{base}::{paradigm}"

    @tool
    def ask_rag(question: str) -> str:
        """Delegate the question to the chunk-RAG agent (Chroma vectors).

        Best for single-section semantic lookups and for negation
        questions when the corpus uses consistent vocabulary. Weak on
        cross-section joins. Returns the RAG agent's natural-language
        answer.
        """
        sub_thread = _sub_thread("rag")
        reset_scratchpad(sub_thread)
        try:
            return rag.ask(question, thread_id=sub_thread)
        except Exception as exc:  # noqa: BLE001 — never let a sub-agent crash router
            return f"(rag sub-agent error: {type(exc).__name__}: {exc})"

    @tool
    def ask_graph(question: str) -> str:
        """Delegate the question to the graph-RAG agent (Neo4j + Cypher).

        Best for cross-section joins (multi-hop, dependency chain,
        shared neighbour, set-difference / negation with structural
        edges). Weak on facts the KGGen extractor dropped. Returns the
        graph agent's natural-language answer.
        """
        sub_thread = _sub_thread("graph")
        reset_scratchpad(sub_thread)
        reset_reach_state(sub_thread)
        try:
            return graph.ask(question, thread_id=sub_thread)
        except Exception as exc:  # noqa: BLE001
            return f"(graph sub-agent error: {type(exc).__name__}: {exc})"

    @tool
    def ask_pageindex(question: str) -> str:
        """Delegate the question to the PageIndex agent (vectorless tree).

        Best for questions whose answer fits inside one markdown
        section ("how many X", "what is X"), and for facts the graph
        extractor dropped. Weak on cross-section joins where its
        tree-walk can hit the recursion cap. Returns the PageIndex
        agent's natural-language answer.
        """
        sub_thread = _sub_thread("pageindex")
        reset_scratchpad(sub_thread)
        try:
            return pageindex.ask(question, thread_id=sub_thread)
        except Exception as exc:  # noqa: BLE001
            return f"(pageindex sub-agent error: {type(exc).__name__}: {exc})"

    return [ask_rag, ask_graph, ask_pageindex, *SCRATCHPAD_TOOLS]


class RouterAgent:
    """LangGraph React agent that routes each question to one or more sub-agents."""

    def __init__(
        self,
        config: Config | None = None,
        rag: RAGAgent | None = None,
        graph: GraphAgent | None = None,
        pageindex: PageIndexAgent | None = None,
    ) -> None:
        self.config = config or load_config()
        self.rag = rag or RAGAgent(self.config)
        self.graph = graph or GraphAgent(self.config)
        self.pageindex = pageindex or PageIndexAgent(self.config)
        self.llm = ChatOpenAI(
            model=self.config.openai.agent_model,
            api_key=self.config.openai.api_key,
            temperature=0,
        )
        self.checkpointer = MemorySaver()
        # Tools close over a holder dict so we can update the router's
        # thread_id per question without rebuilding the agent. Sub-agent
        # threads are derived from the router's thread_id (suffixed with
        # the paradigm) so each question's sub-agent calls are isolated.
        self._thread_holder: dict[str, str] = {"thread_id": "default"}
        self.agent = create_react_agent(
            model=self.llm,
            tools=_build_tools(self.rag, self.graph, self.pageindex, self._thread_holder),
            prompt=with_sections(BASE_PERSONA, ROUTER_SYSTEM_EXTRA),
            checkpointer=self.checkpointer,
        )

    def ask(self, question: str, thread_id: str = "default") -> str:
        return self.ask_with_trace(question, thread_id=thread_id).answer

    def ask_with_trace(self, question: str, thread_id: str = "default") -> AgentRun:
        """Run the router and return the final answer + raw message list.

        Symmetric to the other three agents. The eval runner consumes the
        raw messages via `eval.trace.extract_trace` to compute tool-call
        counts (here: which paradigm sub-agents the router consulted).
        """
        self._thread_holder["thread_id"] = thread_id
        set_active_thread(thread_id)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 16,
            },
        )
        messages = result["messages"]
        answer = ""
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "ai" and getattr(msg, "content", None):
                answer = msg.content if isinstance(msg.content, str) else str(msg.content)
                break
        return AgentRun(answer=answer, messages=list(messages))
