"""Graph agent: text-to-Cypher LangGraph React agent over Neo4j."""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from graph_rag_graph_agent.agents.common import BASE_PERSONA, with_sections
from graph_rag_graph_agent.agents.memory import (
    SCRATCHPAD_TOOLS,
    set_active_thread,
)
from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.schema import GraphSchema, fetch_schema
from graph_rag_graph_agent.graph.tools import build_graph_tools


# Few-shots intentionally use placeholder names like <SUBJECT>, <REL_TYPE>
# so we do not leak any domain-specific entities into the prompt. The real
# vocabulary (node labels, rel types, sample entities) is supplied to the
# model separately via the live schema dump.
_FEW_SHOTS = """\
Example Cypher idioms (replace <PLACEHOLDERS> with real names from the schema):

Q: What is X related to via some specific relationship R?
Cypher:
  MATCH (s:Entity {name: '<SUBJECT>'})-[:<REL_TYPE>]->(t:Entity)
  RETURN t.name AS result

Q: Which entities reach X transitively (1-4 hops, any relationship)?
Cypher:
  MATCH (s:Entity)-[*1..4]->(:Entity {name: '<TARGET>'})
  RETURN DISTINCT s.name AS reaches

Q: Which entities are connected to both X and Y (shared neighbour)?
  # Do not commit to a specific rel type - the two sides may use different
  # edges. Use `-->` (or `<--` / `-[r]->`) so you catch any relationship.
Cypher:
  MATCH (:Entity {name: '<A>'})-->(t:Entity)<--(:Entity {name: '<B>'})
  RETURN DISTINCT t.name AS shared

Q: How many outgoing neighbours does X have via relationship R?
Cypher:
  MATCH (:Entity {name: '<SUBJECT>'})-[:<REL_TYPE>]->(t:Entity)
  RETURN count(DISTINCT t) AS count

Q: Which entities do NOT have relationship R to X?
  # Use a candidate pool (entities that themselves participate in the graph)
  # to avoid enumerating every leaf node.
Cypher:
  MATCH (s:Entity)-->()
  WITH DISTINCT s
  WHERE NOT (s)-[:<REL_TYPE>]->(:Entity {name: '<TARGET>'})
  RETURN s.name AS negative ORDER BY s.name LIMIT 20
"""


def _system_prompt(schema: GraphSchema) -> str:
    cypher_guidance = f"""\
Retrieval strategy:
- You have a knowledge graph in Neo4j with a single node label `Entity`
  and a `name` property. All information lives in relationship EDGES
  between entities. Relationship directions matter.
- To answer questions, WRITE AND RUN Cypher queries via `run_cypher`. You
  may call it multiple times to refine.

Schema-first workflow (important - do this before guessing Cypher):
1. Identify the entities in the question. If an entity is referred to by
   description rather than exact name (e.g. "the team that handles X",
   "the ADR about Y"), call `resolve_entity` first and pick the top
   match. If a short/long form ambiguity exists, `list_entities_like`
   helps.
2. Before writing any targeted `-[:REL_TYPE]->` pattern, call
   `neighbourhood(<entity_name>)` on the key entity. This tells you which
   relationship types actually exist for that entity and in which
   direction - in this graph, the "right" rel type is rarely the one
   that first comes to mind. Do NOT guess rel type names from English
   verbs in the question ("authored", "implements", "manages") - ask the
   graph.
3. Then write your Cypher, using the rel types and directions you just
   observed.

Query-writing rules:
- Entity names are case-sensitive and must match exactly. If Cypher
  returns 0 rows, double-check the name (via `resolve_entity`) before
  blaming the rel type.
- Attributes like role / title / status / version are sometimes modelled
  as a NEIGHBOUR entity, not a property. If `x.<attr>` returns null, try
  `MATCH (x)-->(t:Entity) RETURN t.name` and look for an entity that
  reads like that attribute.
- For multi-hop questions use variable-length patterns like
  `-[:REL_A|REL_B*1..4]->`. ALWAYS constrain the rel types on
  variable-length paths - bare `-[*1..4]->` picks up teams,
  infrastructure, documents and noise, turning a clean answer into a
  dozen unrelated entities.
- When `run_cypher` returns NOTE lines warning that a rel type or
  property does not exist, TRUST them and rewrite the query using the
  suggested alternatives - don't keep re-submitting minor variants of
  the same wrong vocabulary.
- Use the scratchpad tools to stash intermediate results (e.g. a set of
  candidate entity names) while working through complex questions.
- When a result set is larger than ~10 rows, SUMMARISE it rather than
  dumping every row, unless the question specifically asks to
  enumerate.

{schema.render_for_prompt()}

{_FEW_SHOTS}

When you've gathered enough, give a concise natural-language answer,
and briefly mention the key Cypher pattern(s) you used.
"""
    return with_sections(BASE_PERSONA, cypher_guidance)


class GraphAgent:
    """LangGraph React agent that answers by generating and executing Cypher."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self.schema = fetch_schema(self.config)
        self.llm = ChatOpenAI(
            model=self.config.openai.agent_model,
            api_key=self.config.openai.api_key,
            temperature=0,
        )
        self.checkpointer = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=[*build_graph_tools(self.config), *SCRATCHPAD_TOOLS],
            prompt=_system_prompt(self.schema),
            checkpointer=self.checkpointer,
        )

    def ask(self, question: str, thread_id: str = "default") -> str:
        set_active_thread(thread_id)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={
                "configurable": {"thread_id": thread_id},
                # Hard cap on ReAct steps so the agent can't loop forever on
                # a pathological question.
                "recursion_limit": 24,
            },
        )
        messages = result["messages"]
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "ai" and getattr(msg, "content", None):
                return msg.content if isinstance(msg.content, str) else str(msg.content)
        return ""
