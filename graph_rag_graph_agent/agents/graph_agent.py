"""Graph agent: text-to-Cypher LangGraph React agent over Neo4j."""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from graph_rag_graph_agent.agents.common import AgentRun, BASE_PERSONA, with_sections
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

Q: Which entities reach X transitively via a relationship-family F
   (e.g. all the "depends-on" / "relies-on" spellings KGGen emitted)?
  # PREFERRED: call the `reach` tool. It builds the rel-type union
  # automatically from a concept phrase and runs the variable-length
  # Cypher for you, so the agent cannot accidentally write Cypher with
  # different rel types than the union it just looked up:
  #   reach(entity_name='<TARGET>', concept='<verb>',
  #         direction='incoming', depth=4)
  # This collapses the recipe into one tool call. Use it whenever the
  # question is transitive ("directly or indirectly", "downstream",
  # "reaches", "is built on top of") AND the verb plausibly has multiple
  # rel-type spellings.
  #
  # FALLBACK (only when `reach` returns nothing useful, or you need a
  # custom WHERE clause): write Cypher by hand. Get the union from the
  # "Concept clusters" section of the schema or via
  # `find_rel_types_like('<verb>')`, then substitute below. Never use
  # bare `-[*1..N]->` without a rel-type union - it pulls in teams,
  # infrastructure, documents and other noise and produces a wrong
  # answer with high confidence.
Cypher:
  MATCH (s:Entity)-[:<REL_A>|<REL_B>|<REL_C>*1..4]->(:Entity {name: '<TARGET>'})
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

Q: Which X do NOT have relationship R to Y?
  # PREFERRED: use the `set_difference` tool. KGGen graphs have noisy
  # synonymous rel types (e.g. IS_BUILT_WITH | IS_DEVELOPED_IN |
  # IS_IMPLEMENTED_IN | BUILT_USING | IS_WRITTEN_IN all express
  # "implemented in"). A single-spelling `NOT EXISTS { -[:REL_TYPE]-> }`
  # silently matches NOTHING when the spelling is wrong and hands back
  # the full candidate set as "the answer". `set_difference` makes the
  # candidate set, the exclude set, and the overlap explicitly visible
  # in one tool call so the failure mode becomes detectable instead of
  # silent.
  # STEP 1: write the candidate Cypher (positive set), aliased
  #   `RETURN <expr> AS name`.
  # STEP 2: write the exclude Cypher, ALWAYS using the FULL rel-type
  #   union from `find_rel_types_like('<verb>')` or the Concept
  #   clusters - never a single spelling. Same `RETURN ... AS name`.
  # STEP 3: call `set_difference(candidate_cypher, exclude_cypher)`.
  #   The result line `8 candidates - 5 excluded (overlap) = 3 in result`
  #   tells you immediately whether the exclude set was sized
  #   plausibly. If excluded=0 the rel-type union is wrong - go back to
  #   `find_rel_types_like` and widen it.
  #
  # Example shape (placeholder verbs - substitute the real rel-type
  # union from the schema for your concept):
  #   set_difference(
  #     candidate_cypher="MATCH (:Entity {name: '<Y>'})-[:<REL_M>]->"
  #                      "(s:Entity) RETURN s.name AS name",
  #     exclude_cypher="MATCH (s:Entity)-[r]->(:Entity {name: '<Z>'}) "
  #                    "WHERE type(r) IN "
  #                    "['<REL_A>','<REL_B>','<REL_C>'] "
  #                    "RETURN s.name AS name",
  #   )
  #
  # FALLBACK (only when the question doesn't fit the diff shape -
  # rare): manual Cypher with explicit name list:
Cypher:
  MATCH (<candidate pattern>)
  WITH <candidate>.name AS name
  WHERE NOT name IN [<names from step 2, comma-separated single-quoted>]
  RETURN name

Q: A 3-hop question like "what <attr> does the <X> <verbed-by> <PERSON> have?"
  # 3-hop decomposition recipe. Do NOT write one mega-MATCH; the rel-type
  # vocabulary is too noisy for that to succeed in one shot.
  # STEP 1: resolve the middle entity with one query, stash its name:
  #   MATCH (:Entity {name: '<PERSON>'})<-[r]-(m:Entity)
  #   WHERE type(r) IN ['<REL_A>', '<REL_B>']  // from find_rel_types_like
  #   RETURN m.name
  #   -> `scratchpad_write("middle_entity", "<name>")`
  # STEP 2: query from the middle entity to the final attribute, using
  #   `neighbourhood(<name>)` first if you don't know which rel type
  #   carries the attribute:
  #   MATCH (:Entity {name: '<middle>'})-[:<REL_C>]->(t:Entity)
  #   RETURN t.name
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
3. When the question's verb might map to several spellings (common for
   KGGen-extracted graphs - e.g. "depends on" might surface as
   DEPENDS_ON, RELIES_ON), use the FULL union of every spelling in your
   Cypher. The "Concept clusters" section of the schema dump shows
   pre-computed unions; for cross-cluster synonyms or quick lookups call
   `find_rel_types_like('<verb>')`.
4. Then write your Cypher, using the rel types and directions you just
   observed.

CRITICAL: when you call `find_rel_types_like` or look at the Concept
clusters and see e.g. `DEPENDS_ON | RELIES_ON | IS_DEPENDENCY_OF`, your
Cypher MUST use that exact union. Do not silently substitute different
rel-type spellings (e.g. INTEGRATES_WITH, SUPPORTS) that "feel close" -
those represent different concepts in this graph and will return the
wrong entity set. If the looked-up union is empty or wrong, say so and
try a different concept word; do not invent rel types.

When to use the `reach` tool (NARROW criteria - read carefully):
- Use `reach` ONLY when the question is EXPLICITLY transitive: it must
  contain phrases like "directly or transitively", "directly or
  indirectly", "downstream of", "everything that depends on", or
  "transitive closure". For "X depends on Y" without "directly or
  indirectly" the answer is single-hop and `reach` is overkill.
- Aliases are folded automatically: `reach` (and `neighbourhood`,
  `resolve_entity`) silently union over node-name spellings (e.g.
  `Auth Service` and `Authentication Service`, `Payments Service`
  and `service-payments-service`). You do NOT need to call `reach`
  twice with two spellings - the result preamble lists which aliases
  were unioned. If you don't see your expected entity in the alias
  list, that's evidence the spelling itself is novel; try
  `list_entities_like('<partial>')`.
- ZERO-MATCH RULE: if `reach` returns "(no matches)" on an entity,
  do NOT call `reach` on that same entity again with a different
  concept word. The tool will refuse, and rightly so - in v4 traces
  the second/third concept-word attempt almost never recovered. The
  issue is the relation DIRECTION (try the other direction once),
  the wrong source entity, or that the answer truly is empty. After
  one zero-match call `neighbourhood(<X>)` and read the actual edges.
- For categorical questions ("which **services** depend on X",
  "which **databases** does Y use"), pass `name_filter=<keyword>` so
  results are scoped to entity names containing the keyword. Without
  this, an unscoped `reach('Redis', 'use', incoming)` returns Logistics
  Team, Data Lineage Tracking Service and other non-services that
  happen to share a "use"-flavoured edge with Redis.
- Watch for the "matched rel-type union is semantically incoherent"
  NOTE in `reach` output. It fires when a concept word pulled in two
  distinct relations (e.g. "developed" matching DEVELOPED_BY person
  AND DEVELOPED_IN language). When you see it, switch to
  decomposition - the variable-length traversal will mix the two
  rel-classes and produce wrong answers.
- Do NOT use `reach` for single-hop attribute lookups ("what language
  is X built with?", "who manages X?", "which cache does X use?").
  Those are one-edge questions - call `neighbourhood(<X>)` and write
  Cypher with the right rel type from the result. `reach` does
  variable-length paths and can over-traverse; you'll get noise.
- Do NOT use `reach` for 3-hop chains where each hop is a different
  relation. Anti-example (gold-016 in v4): "which language is the
  service that is managed by the Platform Team and depends on the
  Data Lineage Service built with?" - three different verbs (manage,
  depend, built-with), three different rel-classes, no single
  concept word covers them. Decompose: resolve the middle entity
  with one targeted `run_cypher` (`MATCH (Platform Team)-[:MANAGES]->
  (s)-[:DEPENDS_ON]->(Data Lineage Service) RETURN s.name`), stash
  via `scratchpad_write`, then a second Cypher for the language hop.

Question-shape triggers (which recipe applies):
- "Which X reach/depend-on/... Y directly OR INDIRECTLY/transitively?"
  -> use `reach(entity_name='Y', concept='<verb>', direction='incoming')`
  (or outgoing if Y is the source). If the question scopes to a
  category ("which **services**", "which **teams**"), pass the
  category as `name_filter` so non-matching entities are excluded.
- "Which X do NOT <verb> Y?" -> use the `set_difference` tool (few-shot
  below). It runs your candidate and exclude Cyphers in one call and
  returns the diff with both source-set sizes and the overlap visible.
  Do NOT rely on a single-spelling `NOT EXISTS {{ -[:REL_TYPE]-> }}`
  filter - the KGGen graph has multiple synonymous rel-type spellings
  and a single-spelling NOT EXISTS silently returns every candidate
  (the v4/v5 negation failure mode). Always populate the exclude
  Cypher's rel-type union from `find_rel_types_like('<verb>')` or the
  Concept clusters - the WHERE type(r) IN [...] list must contain
  EVERY spelling the schema offers for that concept.
- Questions that chain 3 or more entities (e.g. "what <attr> does the
  <X> <verbed-by> <PERSON> have?") -> use the 3-hop decomposition
  recipe (few-shot below): resolve the middle entity in one Cypher
  call, stash it in the scratchpad, then query from there. Do NOT use
  `reach` for these - the multiple hops have different concept
  meanings (e.g. "developed_by" -> person and "developed_in" ->
  language are both "develop" but different relations).

Query-writing rules:
- Entity names are case-sensitive and must match exactly. If Cypher
  returns 0 rows, double-check the name (via `resolve_entity`) before
  blaming the rel type.
- Attributes like role / title / status / version are sometimes modelled
  as a NEIGHBOUR entity, not a property. If `x.<attr>` returns null, try
  `MATCH (x)-->(t:Entity) RETURN t.name` and look for an entity that
  reads like that attribute.
- For TRANSITIVE multi-hop questions ("directly or indirectly",
  "transitively"), prefer `reach` over hand-written Cypher. For
  targeted multi-hop questions where each hop is a different relation
  (e.g. "person developed service developed in language"), DECOMPOSE
  with the 3-hop recipe below - do not pass through `reach`.
  When you write Cypher with variable-length patterns like
  `-[:REL_A|REL_B*1..4]->`, ALWAYS constrain the rel types - bare
  `-[*1..4]->` picks up teams, infrastructure, documents and noise,
  turning a clean answer into a dozen unrelated entities. Populate the
  rel-type union from the Concept clusters or
  `find_rel_types_like(<verb>)`, not from a guess.
- When `run_cypher` returns NOTE lines warning that a rel type or
  property does not exist, TRUST them and rewrite the query using the
  suggested alternatives - don't keep re-submitting minor variants of
  the same wrong vocabulary.
- Use the scratchpad tools to stash intermediate results (e.g. a set of
  candidate entity names, or the middle entity in a decomposed 3-hop
  query) while working through complex questions.
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
        return self.ask_with_trace(question, thread_id=thread_id).answer

    def ask_with_trace(self, question: str, thread_id: str = "default") -> AgentRun:
        """Run the agent and return both the final answer and the raw message list.

        The eval runner uses the raw messages to extract tool-call telemetry
        (counts, Cypher queries, find_rel_types_like coverage, recursion-limit
        signal). `ask` is a thin wrapper around this for non-eval callers.
        """
        set_active_thread(thread_id)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={
                "configurable": {"thread_id": thread_id},
                # Hard cap on ReAct steps so the agent can't loop forever on
                # a pathological question. 3-hop questions legitimately need
                # more than 24 steps once you account for entity-resolution
                # plus neighbourhood-inspection plus two or three Cypher
                # iterations; 40 preserves the runaway-loop guard while
                # giving multi-hop reasoning room to breathe.
                "recursion_limit": 40,
            },
        )
        messages = result["messages"]
        answer = ""
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "ai" and getattr(msg, "content", None):
                answer = msg.content if isinstance(msg.content, str) else str(msg.content)
                break
        return AgentRun(answer=answer, messages=list(messages))
