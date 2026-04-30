"""Chunk-RAG agent: LangGraph React agent over the Chroma wiki index."""

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
from graph_rag_graph_agent.rag.retriever import WikiRetriever

RAG_SYSTEM_EXTRA = """\
Retrieval strategy:
- Use `search_wiki` to find passages relevant to the user's question.
  The corpus is split into chunks carrying section-path metadata
  (e.g. "# <Page> > ## <Section> > ### <Subsection>"); search returns the
  top-k chunks ranked by semantic similarity.
- Chunk retrieval is weak at multi-hop questions (e.g. "entities that
  depend on entities that depend on X"). When you need to connect facts
  across different pages, issue MULTIPLE targeted `search_wiki` calls with
  different query formulations and combine the results yourself.
- Use the scratchpad to stash candidate entity names / findings while
  working through a multi-step question.
- Default k is 5; raise it to 8-10 for broad or enumerating questions.
- When a result set is large, SUMMARISE rather than dumping every chunk.

Example query strategies (replace <PLACEHOLDERS> with topics from the
question):

Q: What does X do / what is X?
  → search_wiki("<X> overview purpose") with k=5

Q: Which entities depend on / relate to X (multi-hop)?
  → search_wiki("<X> dependencies") then
    search_wiki("services that depend on <X>") then
    for each candidate found, search_wiki("<candidate> dependencies")
    to follow the chain.

Q: Which entities share a property with X and Y (shared neighbour)?
  → search_wiki("<X> <property>") and search_wiki("<Y> <property>")
    then intersect the entities mentioned.

Q: Which entities do NOT have property/relation R?
  → enumerate the candidate pool with
    search_wiki("list of <entity type>") then for each candidate
    search_wiki("<candidate> <R>") and keep the ones with no hits.
"""


def _build_tools(retriever: WikiRetriever) -> list[Any]:
    @tool
    def search_wiki(query: str, k: int = 5) -> str:
        """Semantic search the company wiki. Returns top-k chunks with source citations.

        Args:
            query: natural-language search query.
            k: number of chunks to return (1-10, default 5).
        """
        k = max(1, min(int(k), 10))
        return retriever.search_formatted(query, k=k)

    return [search_wiki, *SCRATCHPAD_TOOLS]


class RAGAgent:
    """LangGraph React agent that answers using chunk retrieval over the wiki."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self.retriever = WikiRetriever()
        self.llm = ChatOpenAI(
            model=self.config.openai.agent_model,
            api_key=self.config.openai.api_key,
            temperature=0,
        )
        self.checkpointer = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=_build_tools(self.retriever),
            prompt=with_sections(BASE_PERSONA, RAG_SYSTEM_EXTRA),
            checkpointer=self.checkpointer,
        )

    def ask(self, question: str, thread_id: str = "default") -> str:
        """Run the agent on a question and return its final answer string."""
        return self.ask_with_trace(question, thread_id=thread_id).answer

    def ask_with_trace(self, question: str, thread_id: str = "default") -> AgentRun:
        """Run the agent and return both the final answer and the raw message list.

        Mirrors `GraphAgent.ask_with_trace`. The eval runner consumes the raw
        messages via `eval.trace.extract_trace` to compute tool-call counts,
        recursion-limit signal, and step-at-first-relevant-match.
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
