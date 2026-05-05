"""PageIndex agent: vectorless tree-of-contents reasoning RAG over the corpus.

Symmetric to `RAGAgent` and `GraphAgent`: same `BASE_PERSONA`, same
scratchpad tools, same `ask` / `ask_with_trace` shape. Uses three tools
adapted from VectifyAI/PageIndex's canonical agentic example
(`get_document` / `get_document_structure` / `get_section_content`),
re-shaped from PDF pages to markdown nodes.
"""

from __future__ import annotations

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
from graph_rag_graph_agent.pageindex.store import PageIndexStore

# v7 introduces this paradigm. Few-shots use placeholders so we don't
# leak corpus-specific vocabulary into the prompt; the live tree-of-
# contents (titles + summaries) is provided to the agent on demand via
# `get_document_structure`, paradigm-symmetric to how `GraphAgent`
# receives the live schema dump.
PAGEINDEX_SYSTEM_EXTRA = """\
Retrieval strategy:
- The corpus is indexed as a hierarchical "table of contents" (PageIndex
  tree). There is NO vector search and NO chunking. Each tree node
  carries a title, a short summary, a node_id, and a body of markdown
  text. Parent nodes have child nodes; you navigate by reading the
  table of contents and then descending into specific sections.
- You answer by REASONING over the tree. Read the table of contents,
  pick the candidate node_ids whose titles + summaries match what the
  question is asking about, then call `get_section_content` on each to
  read the actual text.

Tool order (do this on every question unless you've already cached
the structure for this thread):

  1. `get_document_structure()` - returns the full tree (titles +
     summaries + node_ids), no body text. Read it once, identify
     candidate node_ids based on title/summary relevance.
  2. `get_section_content(node_id)` - returns the full body text of
     one node (and its descendants). Call this for each candidate
     section you identified in step 1. You may call it multiple times
     for different node_ids.
  3. Synthesise the answer from the section contents you read.

`get_document()` is a one-call orientation - root titles + total node
count + doc description. Useful on the first question of a session if
you want a flavour check; rarely needed once you've called
`get_document_structure` since that returns a superset.

Search strategy by question shape:

Q: What is X / what does X do? (factual, single-section)
  -> get_document_structure(); pick the node whose title matches X
     (or whose summary clearly mentions X); get_section_content on it.

Q: Which entities depend on / relate to X (multi-hop)?
  -> get_document_structure(); pick the node about X AND any nodes
     whose summary mentions a relationship to X (services, teams);
     get_section_content on each. Combine the facts manually -
     the tree is a navigation aid, the joining-up is your job.

Q: Which entities are connected to BOTH X and Y (shared neighbour)?
  -> get_document_structure(); pull the X section AND the Y section
     via get_section_content; intersect what each mentions.

Q: Which entities do NOT have property/relation R?
  -> get_document_structure(); identify the candidate pool from
     section titles (e.g. all "service-*" sections); for each
     candidate, get_section_content and check whether R is mentioned.
     Keep the ones where R is absent.

Q: How many entities have property P?
  -> Identify the candidate pool from the structure (the titles list
     itself is often the count). Verify by reading the relevant
     sections. Always enumerate matched names alongside the count.

Notes on cost and budget:

- The structure is one tool call's worth of tokens (titles + short
  summaries). Read it once, stash important node_ids via the
  scratchpad if you'll need them later in the session.
- `get_section_content` returns FULL body text for a node and its
  descendants. Prefer narrow node_ids (leaves) over root nodes; reading
  a root pulls in everything below it.
- If the structure clearly answers the question (e.g. "list of services"
  is just the top-level service-* titles), do not call
  `get_section_content` unnecessarily.
- Use the scratchpad tools to stash candidate node_ids and
  intermediate findings for multi-step questions.
- When a result set is large, SUMMARISE rather than dumping every section.

When you've gathered enough, give a concise natural-language answer,
and briefly mention which node_ids you read.
"""


def _build_tools(store: PageIndexStore) -> list[Any]:
    @tool
    def get_document() -> str:
        """Return concise corpus-level metadata (description, root titles, node count).

        Use as a one-call orientation. For navigation, prefer
        `get_document_structure` which returns the full table of contents.
        """
        return store.render_metadata()

    @tool
    def get_document_structure() -> str:
        """Return the full tree of contents: titles + summaries + node_ids.

        Body text is NOT included to keep the response compact. Use this
        as the main navigation aid: skim it, pick candidate node_ids, then
        call `get_section_content(node_id)` to read each candidate's body.
        """
        return store.render_structure()

    @tool
    def get_section_content(node_id: str, include_descendants: bool = True) -> str:
        """Return the full body text of one tree node (by node_id).

        Args:
            node_id: the 4-digit zero-padded id from the tree (e.g. "0042").
            include_descendants: if True (default) also concatenates the
                body text of all descendants, so a single call on a parent
                returns the entire subtree. Set False for just this node.
        """
        nid = (node_id or "").strip()
        return store.get_section(nid, include_descendants=include_descendants)

    return [get_document, get_document_structure, get_section_content, *SCRATCHPAD_TOOLS]


class PageIndexAgent:
    """LangGraph React agent that answers via tree-of-contents reasoning."""

    def __init__(
        self,
        config: Config | None = None,
        store: PageIndexStore | None = None,
    ) -> None:
        self.config = config or load_config()
        self.store = store or PageIndexStore.load()
        self.llm = ChatOpenAI(
            model=self.config.openai.agent_model,
            api_key=self.config.openai.api_key,
            temperature=0,
        )
        self.checkpointer = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=_build_tools(self.store),
            prompt=with_sections(BASE_PERSONA, PAGEINDEX_SYSTEM_EXTRA),
            checkpointer=self.checkpointer,
        )

    def ask(self, question: str, thread_id: str = "default") -> str:
        return self.ask_with_trace(question, thread_id=thread_id).answer

    def ask_with_trace(self, question: str, thread_id: str = "default") -> AgentRun:
        """Run the agent and return both the final answer and the raw message list.

        Symmetric to `RAGAgent.ask_with_trace` and `GraphAgent.ask_with_trace`.
        The eval runner consumes the raw messages via `eval.trace.extract_trace`
        to compute tool-call counts, recursion-limit signal, and
        per-paradigm adoption counters (here: `pageindex_section_calls`).
        """
        set_active_thread(thread_id)
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
