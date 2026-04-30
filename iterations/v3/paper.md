# Automated Chunk-RAG vs. Automated Graph-RAG: A Controlled Comparison over a Shared Markdown Corpus

## Changelog (v3)

- eval/trace.py: new module - extracts per-question tool-call trace, Cypher
  telemetry, recursion-limit signal, and `find_rel_types_like` coverage from
  the agent message list (read-only; no behavioural change to either agent).
- eval/oracle.py: new module - executes each gold question's `seed_cypher`
  against the live extracted graph and attributes the row to one of
  `agent_ok`, `agent_miss`, `extraction_miss`, `no_oracle`.
- agents/{graph,rag}_agent.py: added symmetric `ask_with_trace` returning
  the raw langgraph message list alongside the answer; `ask` is now a thin
  wrapper. No prompt or tool change.
- eval/run.py: stores trace + oracle attribution per question.
- eval/report.py: new sections for tool-call counts, failure attribution,
  and `find_rel_types_like` coverage; per-question detail surfaces oracle
  status and step-cap signal.
- eval_data/shopflow_gold.yaml: added `concepts_in_question` per question.

## Changelog (v2)

- graph_agent.py: recursion_limit 24 → 40
- graph/tools.py: added find_rel_types_like
- graph_agent.py: three new few-shots + recipe prose
- eval_data/shopflow_gold.yaml: +20 questions

**Abstract (v3).** v3 is a diagnostic-only iteration: the agents are
unchanged, but the eval pipeline now attributes every gold row to a cause.
Each gold question carries a `seed_cypher` that doubles as an oracle
against the live extracted graph, splitting graph-agent failures into
`extraction_miss` (gold answer not reachable from the graph) and
`agent_miss` (reachable but the agent answered wrong; recoverable with
reasoning improvements). The eval also records per-question tool-call
counts, every Cypher query the agent ran, the recursion-limit signal, and
whether the graph agent invoked `find_rel_types_like` for each concept the
gold author flagged as needing a rel-type union. Re-running the v2 set with
v3 instrumentation yields graph **0.72** vs. RAG **0.47** (v2: 0.70 /
0.45) — within run-to-run nondeterminism noise, confirming the
instrumentation is non-perturbing. New attribution: of 30 graph rows,
**19 agent_ok, 10 agent_miss, 1 extraction_miss**. The negation cell
(0.50, n=4) has **zero** extraction-bound rows — its ceiling is 1.0 and
the gap is purely agent-reasoning-bound. The graph agent invoked
`find_rel_types_like` for only **12 of 42** concepts flagged as needing a
rel-type union (28%); on `gold-019` the tool was probed but the agent
then ran a Cypher with `INTEGRATES_WITH|SUPPORTS` instead of the
returned `DEPENDS_ON|RELIES_ON` family — i.e. probing is necessary but
not sufficient. Run metadata: `20260430T192426Z-a63891`.

**Abstract (v2 - retained for reference).** We compare two LangGraph
ReAct agents that answer natural-language questions over the same
Markdown corpus but index it very differently: a chunk-RAG agent backed
by a Chroma vector store, and a graph-RAG agent that writes Cypher
against a Neo4j graph extracted *automatically* from the same Markdown
by KGGen (Mo et al., 2025). Because extraction on both sides is fully
automated, any difference reflects the combined effect of
(a) representation/extraction and (b) reasoning strategy — not a
human-idealised graph. On a **30-question** hand-curated gold set across
seven categories, the graph agent scores **0.70** (mean judge grade) vs.
the RAG agent's **0.45**, with somewhat higher tail latency for the graph
agent (p95 **34.8s** vs. **20.3s**). The graph agent retains an edge on
multi-hop and counted queries; with larger per-category *n* (4–5), the
earlier n=1 cells in `multi_hop_3` and `negation` are superseded as
stable estimates. v2 run metadata: `20260422T151717Z-71aee8`.

## 1. Introduction

Retrieval-augmented generation (RAG) over semantically chunked text is the
default context-retrieval strategy for LLM agents. An alternative is to extract
a knowledge graph from the same source text and let the agent retrieve via
structured queries. Prior reports of "graph-RAG wins" often compare a
hand-authored graph to off-the-shelf chunking, conflating *extraction quality*
with *paradigm choice*. We hold extraction effort constant (both sides fully
automated from the same Markdown) and ask: on a multi-category question set
designed to stress joins, aggregation, and negation, how does each side fare?

## 2. Methods

### 2.1 Corpus

The corpus is a synthetic enterprise wiki for a fictional e-commerce company
("ShopFlow"): 41 Markdown files (~3 400 lines total) describing services,
teams, people, architecture decision records, databases, and infrastructure.

### 2.2 Indexing pipelines (both automated)

* **Chunk-RAG.** Markdown → chunks → OpenAI `text-embedding-3-small` →
  persisted Chroma collection. Retrieval via a `search_wiki` tool.
* **Graph-RAG.** The same Markdown is processed by KGGen (Mo et al., 2025),
  which emits a single-label (`:Entity{name}`) graph with free-text
  relationship types (589 `MERGE … CREATE` statements; ~1 relationship per
  statement). The graph is loaded into Neo4j and exposed to the agent through
  a `run_cypher` tool with read-only pre-flight validation against the live
  schema, plus paradigm-native helpers (`resolve_entity`, `neighbourhood`,
  `list_entities_like`, `list_relationship_types`, **`find_rel_types_like`**).

### 2.3 Agents

Both agents are LangGraph ReAct agents (`gpt-4o-mini`, temperature 0) with
shared scratchpad tools and a LangGraph `MemorySaver` checkpointer. The
chunk-RAG agent uses a **24-step** recursion cap; the graph agent uses a
**40-step** cap so multi-hop questions have room for entity resolution,
neighbourhood inspection, and several Cypher iterations without hitting the
guard rail. System prompts are symmetrical: same persona skeleton, same
answer-shape contract, same placeholder-style few-shots (`<SUBJECT>`,
`<REL_TYPE>`) so that neither prompt leaks corpus-specific vocabulary. The
graph agent additionally receives a live schema dump (node labels, relationship
types, property keys) and, in v2, three extra **recipes** in the few-shot block:
3-hop decomposition (scratchpad-bridged queries), transitive closure (union of
rel types from `find_rel_types_like` before variable-length paths), and
negation as set subtraction rather than a single fragile `NOT EXISTS` spelling.
The RAG agent learns the vocabulary from tool returns. Neither agent's code
references any entity name from the corpus.

### 2.4 Evaluation

We use a **30-question** hand-curated gold set (`eval_data/shopflow_gold.yaml`)
whose expected answers are verifiable in *both* the Markdown and the extracted
graph. Questions span seven categories: `one_hop`, `multi_hop_2`, `multi_hop_3`,
`dependency_chain`, `shared_neighbor`, `aggregation_count`, `negation`. An
LLM-as-judge (`gpt-4o`) grades each response as correct (1), partial (0.5), or
wrong (0) against the expected answer and the expected key entities. v3 run
metadata: `20260430T192426Z-a63891`. v2 run (kept for reference and for the
comparison columns in §3.1): `20260422T151717Z-71aee8`.

## 3. Results (v3 run)

### 3.1 Accuracy by category

Per-category means use **n=4** or **n=5** per cell. v3 column is the
re-run with v3 instrumentation; v2 column is the prior frozen run. The
comparison is for sanity (the agents are unchanged); within run-to-run
nondeterminism a single-verdict flip in an n=4 cell shifts the mean by
0.25.

| Category            | RAG (v3)   | RAG (v2)   | Graph (v3) | Graph (v2) |
| ------------------- | ---------- | ---------- | ---------- | ---------- |
| `one_hop`           | 0.80 (n=5) | 0.80 (n=5) | 0.80 (n=5) | 0.80 (n=5) |
| `multi_hop_2`       | 0.10 (n=5) | 0.00 (n=5) | **0.80** (n=5) | 0.80 (n=5) |
| `multi_hop_3`       | 0.25 (n=4) | 0.25 (n=4) | **1.00** (n=4) | 0.75 (n=4) |
| `dependency_chain`  | 0.75 (n=4) | 0.75 (n=4) | 0.50 (n=4) | 0.50 (n=4) |
| `shared_neighbor`   | 0.88 (n=4) | 0.88 (n=4) | 0.88 (n=4) | 1.00 (n=4) |
| `aggregation_count` | 0.12 (n=4) | 0.25 (n=4) | 0.50 (n=4) | 0.75 (n=4) |
| `negation`          | 0.38 (n=4) | 0.25 (n=4) | **0.50** (n=4) | 0.25 (n=4) |
| **Overall**         | **0.47**   | **0.45**   | **0.72**   | **0.70**   |

### 3.2 Latency

| Agent | mean (s, v3) | p95 (s, v3) | mean (s, v2) | p95 (s, v2) |
| ----- | ------------ | ----------- | ------------ | ----------- |
| RAG   | 10.24        | 18.42       | 11.19        | 20.25       |
| Graph | 8.18         | 20.71       | 12.02        | 34.83       |

The graph agent's v3 latencies are notably lower than v2; this run had
fewer step-cap refusals (which are slow to terminate). Treat the
specific p95 number as run-dependent.

### 3.3 Qualitative patterns

The qualitative patterns from v2 broadly hold; v3's contribution is that
they are now quantified in §5.

* **Factual grounding (1-hop).** Both agents score 0.80; the Payments
  Service language fact (`gold-002`) is the only graph
  `extraction_miss` in the entire set.
* **Composition (2-hop).** Graph 0.80; RAG 0.10 with multiple step-cap
  refusals on author-and-role questions.
* **3-hop.** Graph 1.00 in this run (was 0.75 in v2 — `gold-016` flipped
  from refusal to correct). Variance is real; the cell is not "solved",
  but the trace shows the path that worked: 4–6 tool calls, no
  recursion-cap pressure.
* **Transitive / dependency-chaining.** Graph 0.50, three of four
  failures are agent-bound rel-type mis-unioning (e.g. `gold-019`'s
  `INTEGRATES_WITH|SUPPORTS` instead of `DEPENDS_ON|RELIES_ON` — see
  §5.3). Zero extraction-miss in this category.
* **Negation / set difference.** Graph 0.50 (up from v2's 0.25), all four
  rows have non-empty oracles, so the cell is reasoning-bound, not
  extraction-bound.
* **Shared neighbours.** Graph 0.88; the single miss is a partial that
  enumerates an extra entity rather than a category-level failure.

## 4. Discussion

The overall **0.72 vs. 0.47** gap (n=30) is directionally consistent with
v1 (0.70 vs. 0.40 on 10 questions) and v2 (0.70 vs. 0.45 on 30): graph
retrieval still wins on compositional and counted structure, but RAG
**closed part of the gap** on the larger set because more dependency-
chain and 1-hop questions are tractable for chunk retrieval. Three
qualifiers matter:

1. **Extraction recall is the graph agent's ceiling.** KGGen still misses
   lines that are obvious in Markdown (`gold-002`). We do not patch the graph by
   hand, by design.
2. **Agent-only mitigations are real but not universal.** A higher step budget,
   `find_rel_types_like`, and explicit recipes improve some multi-hop and
   negation items but do not remove failure modes on the hardest set-
   difference prompts or on mis-aligned transitive queries.
3. **N=30 is still moderate.** Category cells are now *interpretable* (n≈4–5)
   rather than single-shot anecdotes, but they remain lab-scale; use them to
   locate failure modes, not to rank production systems.

## 5. Failure attribution (v3)

v3 runs the same agents on the same gold set, with three new diagnostic
artifacts per row.

### 5.1 Headline split

Across n=30 graph rows: **19 agent_ok, 10 agent_miss, 1 extraction_miss,
0 no_oracle**. Per-category split (graph agent):

| Category            | agent_ok | agent_miss | extraction_miss |
| ------------------- | -------- | ---------- | --------------- |
| `one_hop`           | 4        | 0          | 1               |
| `multi_hop_2`       | 4        | 1          | 0               |
| `multi_hop_3`       | 4        | 0          | 0               |
| `dependency_chain`  | 1        | 3          | 0               |
| `shared_neighbor`   | 3        | 1          | 0               |
| `aggregation_count` | 2        | 2          | 0               |
| `negation`          | 1        | 3          | 0               |

The single `extraction_miss` is `gold-002` (Payments Service language),
already called out in v2 §3.3. **Every other failure is agent-bound and
in principle recoverable** — including the entire negation cell and the
entire dependency-chain failure set, which the v2 paper had to discuss
qualitatively.

### 5.2 Tool-call counts (mean per question)

| Category            | rag  | graph |
| ------------------- | ---- | ----- |
| `one_hop`           | 1.0  | 3.0   |
| `multi_hop_2`       | 6.0  | 3.0   |
| `multi_hop_3`       | 9.2  | 6.0   |
| `dependency_chain`  | 6.2  | 3.8   |
| `shared_neighbor`   | 3.0  | 5.5   |
| `aggregation_count` | 5.8  | 4.0   |
| `negation`          | 9.5  | 8.2   |

The graph agent uses fewer tool calls than RAG on every multi-hop and
chain category, consistent with structured retrieval being denser per
call. Negation is the only category where both agents pay similar tool-
call cost.

### 5.3 `find_rel_types_like` coverage

The graph agent invoked `find_rel_types_like` for only **12 of 42**
concepts flagged in the gold YAML as needing a rel-type union (28%).
This empirically confirms a hypothesis from the v2 discussion: the
recipe is prose, and the model skips the discretionary tool call most
of the time even when the question shape demands it. Coverage by
category: `negation` 4/8, `dependency_chain` 3/4, `multi_hop_3` 1/8,
`aggregation_count` 2/4, all others 0–2/n.

A subtler finding visible only with traces: probing the tool is
**necessary but not sufficient**. On `gold-019` ("which services rely on
Payments Service, transitively?") the agent did call
`find_rel_types_like('depend')`, received the `DEPENDS_ON | RELIES_ON |
IS_DEPENDENCY_OF` family, then issued a Cypher using
`INTEGRATES_WITH | SUPPORTS` instead — and answered with the wrong
service set. Schema-time concept clusters (planned for v4) need to be
paired with a mechanism that gets the agent to actually use the cluster,
not just see it.

### 5.4 Run-to-run noise on n=4 cells

The v3 re-run shifted multi_hop_3 0.75→1.00, negation 0.25→0.50,
aggregation_count 0.75→0.50, shared_neighbor 1.00→0.88 vs. v2 — single-
verdict flips in n=4 cells move the cell mean by 0.25. Overall, graph
moved 0.70→0.72, well within nondeterminism. Cells should be read as
indicative; pairwise across iterations, attribution splits are more
stable than the means.

## 6. Conclusion

Holding extraction *effort* constant — both sides fully automated from the
same Markdown — a text-to-Cypher graph agent **still** outperforms chunk-RAG on
this benchmark overall, with the advantage visible in multi-hop structure and
aggregations, while **negation remains difficult for both** under automated
extraction. v3 instruments the eval so future iterations can attribute
lifts to the right cause: extraction recall (out of scope for the agent)
vs. agent reasoning vs. step budget. The v3 attribution shows that the
remaining graph-agent gap on negation, dependency_chain, and parts of
aggregation_count is *agent-bound, not extraction-bound* — which is the
working hypothesis the v4 levers (schema-time concept clustering, a
deterministic `reach` tool, mandatory rel-type unions on variable-length
paths, set-subtraction helpers) are designed to address.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy, C.,
  Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting Knowledge Graphs
  from Plain Text with Language Models*. arXiv:2502.09956.
- LangGraph. <https://langchain-ai.github.io/langgraph/>.
- Neo4j. <https://neo4j.com/docs/>.
- Chroma. <https://docs.trychroma.com/>.
