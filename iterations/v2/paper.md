# Automated Chunk-RAG vs. Automated Graph-RAG: A Controlled Comparison over a Shared Markdown Corpus

## Changelog (v2)

- graph_agent.py: recursion_limit 24 → 40
- graph/tools.py: added find_rel_types_like
- graph_agent.py: three new few-shots + recipe prose
- eval_data/shopflow_gold.yaml: +20 questions

**Abstract.** We compare two LangGraph ReAct agents that answer natural-language
questions over the same Markdown corpus but index it very differently: a
chunk-RAG agent backed by a Chroma vector store, and a graph-RAG agent that
writes Cypher against a Neo4j graph extracted *automatically* from the same
Markdown by KGGen (Mo et al., 2025). Because extraction on both sides is fully
automated, any difference reflects the combined effect of
(a) representation/extraction and (b) reasoning strategy — not a
human-idealised graph. On a **30-question** hand-curated gold set across seven
categories, the graph agent scores **0.70** (mean judge grade) vs. the RAG
agent's **0.45**, with somewhat higher tail latency for the graph agent (p95
**34.8s** vs. **20.3s**). The graph agent retains an edge on multi-hop and
counted queries; with larger per-category *n* (4–5), the earlier n=1 cells in
`multi_hop_3` and `negation` are superseded as stable estimates. Run metadata:
`20260422T151717Z-71aee8`.

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
wrong (0) against the expected answer and the expected key entities. Run
metadata: `20260422T151717Z-71aee8`.

## 3. Results

### 3.1 Accuracy by category

Per-category means use **n=4** or **n=5** per cell; they supersede the v1 paper's
n=1 snapshots for the categories that were expanded.

| Category            | RAG            | Graph          |
| ------------------- | -------------- | -------------- |
| `one_hop`           | 0.80 (n=5)     | 0.80 (n=5)     |
| `multi_hop_2`       | 0.00 (n=5)     | **0.80** (n=5) |
| `multi_hop_3`       | 0.25 (n=4)     | **0.75** (n=4) |
| `dependency_chain`  | 0.75 (n=4)     | 0.50 (n=4)     |
| `shared_neighbor`   | 0.88 (n=4)     | **1.00** (n=4) |
| `aggregation_count` | 0.25 (n=4)     | **0.75** (n=4) |
| `negation`          | 0.25 (n=4)     | 0.25 (n=4)     |
| **Overall**         | **0.45**       | **0.70**       |

### 3.2 Latency

| Agent | mean (s) | p95 (s) |
| ----- | -------- | ------- |
| RAG   | 11.19    | 20.25   |
| Graph | 12.02    | 34.83   |

The graph agent's mean latency remains close to the RAG baseline, but the
p95 is higher — consistent with long multi-tool traces on the hardest
questions (including occasional step-limit refusals under heavy hop depth).

### 3.3 Qualitative patterns

* **Factual grounding (1-hop).** Both agents score 0.80 on five questions; the
  Payments Service language fact (`gold-002`) is still a **graph extraction
  miss** and the graph agent again fails to recover Python from the KG.
* **Composition (2-hop).** The graph agent wins most of the set (0.80); the RAG
  agent still often exhausts its step budget on author-and-role or team-chain
  questions. Where the graph is wrong, it is often **relation mis-interpretation**
  (e.g. wrong "leads" edge vs. the gold team name).
* **3-hop.** With *n=4*, the graph agent is no longer at zero: decomposition and
  extra steps help, but one complex join (`gold-016`) still hit the step limit.
* **Transitive / dependency-chaining.** Results are **mixed and noisy in both
  paradigms**: the RAG agent sometimes over-lists services; the graph agent
  occasionally follows lexically plausible but wrong relationship types, or
  returns refusals on long set-difference questions (`gold-019`, `gold-029`).
* **Negation / set difference.** **Both agents sit at 0.25 (n=4).** The graph
  agent can succeed when dependencies are simply absent in the graph
  (`gold-008`), but questions that require set subtraction over Python +
  management edges still produce wrong universals or refusals (`gold-028`–`gold-030`).
* **Shared neighbours.** The graph agent holds a perfect 1.00; the RAG agent
  is strong but not flawless (0.88), usually from extra entities in the answer.

## 4. Discussion

The overall **0.70 vs. 0.45** gap (n=30) is directionally consistent with v1
(0.70 vs. 0.40 on 10 questions): graph retrieval still wins on compositional
and counted structure, but RAG **closed part of the gap** on the larger set
because more dependency-chain and 1-hop questions are tractable for chunk
retrieval. Three qualifiers matter:

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

## 5. Conclusion

Holding extraction *effort* constant — both sides fully automated from the
same Markdown — a text-to-Cypher graph agent **still** outperforms chunk-RAG on
this benchmark overall, with the advantage visible in multi-hop structure and
aggregations, while **negation remains difficult for both** under automated
extraction. For workflows where joins and counts dominate, graph-RAG remains
attractive; for universal quantification and set subtraction, neither agent is
yet reliable without stronger extraction or dedicated tooling.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy, C.,
  Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting Knowledge Graphs
  from Plain Text with Language Models*. arXiv:2502.09956.
- LangGraph. <https://langchain-ai.github.io/langgraph/>.
- Neo4j. <https://neo4j.com/docs/>.
- Chroma. <https://docs.trychroma.com/>.
