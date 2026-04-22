# Automated Chunk-RAG vs. Automated Graph-RAG: A Controlled Comparison over a Shared Markdown Corpus

**Abstract.** We compare two LangGraph ReAct agents that answer natural-language
questions over the same Markdown corpus but index it very differently: a
chunk-RAG agent backed by a Chroma vector store, and a graph-RAG agent that
writes Cypher against a Neo4j graph extracted *automatically* from the same
Markdown by KGGen (Mo et al., 2025). Because extraction on both sides is fully
automated, any difference reflects the combined effect of
(a) representation/extraction and (b) reasoning strategy — not a
human-idealised graph. On a 10-question hand-curated gold set across seven
categories, the graph agent scores **0.70** (mean judge grade) vs. the RAG
agent's **0.40**, with comparable latency (7.7s vs. 8.4s mean). The graph
agent's advantage is concentrated in 2-hop joins and counted aggregations; both
agents tie on 1-hop lookups and both struggle on 3-hop joins, where KGGen's
extraction recall becomes the binding constraint.

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
  `list_entities_like`, `list_relationship_types`).

### 2.3 Agents

Both agents are LangGraph ReAct agents (`gpt-4o-mini`, temperature 0, 24-step
recursion cap) with shared scratchpad tools and a LangGraph `MemorySaver`
checkpointer. System prompts are symmetrical: same persona skeleton, same
answer-shape contract, same placeholder-style few-shots (`<SUBJECT>`,
`<REL_TYPE>`) so that neither prompt leaks corpus-specific vocabulary. The
graph agent additionally receives a live schema dump (node labels, relationship
types, property keys); the RAG agent learns the vocabulary from tool returns.
Neither agent's code references any entity name from the corpus.

### 2.4 Evaluation

We use a 10-question hand-curated gold set (`eval_data/shopflow_gold.yaml`)
whose expected answers are verifiable in *both* the Markdown and the extracted
graph. Questions span seven categories chosen to expose where chunk retrieval
typically struggles: `one_hop`, `multi_hop_2`, `multi_hop_3`,
`dependency_chain`, `shared_neighbor`, `aggregation_count`, `negation`. An
LLM-as-judge (`gpt-4o`) grades each response as correct (1), partial (0.5), or
wrong (0) against the expected answer and the expected key entities. Run
metadata: `20260418T134710Z-9dc0ac`.

## 3. Results

### 3.1 Accuracy by category

| Category            | RAG          | Graph        |
| ------------------- | ------------ | ------------ |
| `one_hop`           | 0.67 (n=3)   | 0.67 (n=3)   |
| `multi_hop_2`       | 0.00 (n=2)   | **1.00** (n=2) |
| `multi_hop_3`       | 0.00 (n=1)   | 0.00 (n=1)   |
| `dependency_chain`  | 0.50 (n=1)   | 0.50 (n=1)   |
| `shared_neighbor`   | 1.00 (n=1)   | 1.00 (n=1)   |
| `aggregation_count` | 0.00 (n=1)   | **1.00** (n=1) |
| `negation`          | 0.50 (n=1)   | 0.50 (n=1)   |
| **Overall**         | **0.40**     | **0.70**     |

### 3.2 Latency

| Agent | mean (s) | p95 (s) |
| ----- | -------- | ------- |
| RAG   | 8.44     | 13.28   |
| Graph | 7.67     | 12.88   |

Latency is comparable; the graph agent is not materially slower despite doing
multiple Cypher round-trips.

### 3.3 Qualitative patterns

* **Factual grounding (1-hop).** Both paradigms answer cleanly when the fact
  sits in a single retrieved chunk or a single edge (`gold-001`, `gold-003`).
  Both miss the same question (`gold-002`, "what language is Payments Service
  in?") — RAG retrieves the wrong chunk and confidently answers "Java"; the
  graph genuinely doesn't contain the edge (KGGen didn't extract "implemented
  in Python" as a relationship), an *extraction miss*.
* **Composition (2-hop).** The graph agent wins 2/2 (`gold-004`, `gold-005`).
  Semantic retrieval collapses here: to answer "who authored the
  QuickCart-acquisition ADR and what is their role?", chunk retrieval returns
  ADR text rich in "acquisition" tokens but poor in author metadata; the
  agent exhausts its step budget.
* **Aggregation.** "How many services does the Platform Team manage?" is
  where chunk retrieval fails most cleanly: the RAG agent recalls three
  services but confabulates two of them. The graph agent's `MATCH
  (:Entity{name:'Platform Team'})-[:MANAGES]->(s) RETURN count(s), collect(s.name)`
  is a one-shot query.
* **Negation.** Both agents earn only partial credit; the graph agent
  initially over-includes the Auth Service because it fails to filter its
  candidate set through `NOT EXISTS {…}` correctly. This is a *reasoning*
  miss, not an extraction miss.
* **3-hop / transitive.** Both paradigms fail or over-generalise. The graph
  agent returns a noisy mix of unrelated nodes when it falls back to
  variable-length paths without constraining rel types — exactly the failure
  mode its own prompt warns against.

## 4. Discussion

The overall 0.70 vs. 0.40 gap matches the expected structural advantage of
graph retrieval on composed, counted, and comparative queries. Three qualifiers
matter for interpreting this as a general claim:

1. **Extraction recall is the graph agent's ceiling.** KGGen misses facts that
   are present in prose but phrased unusually (e.g. "Implemented in Python" as
   a service-property rather than a typed edge). This is a real,
   paradigm-level cost of fully-automated graph construction. The experiment
   intentionally does not patch the graph by hand, because doing so would
   leak human curation into one side of the comparison.
2. **Chunk RAG's failures here are confabulations, not refusals.** In
   `gold-002` and `gold-007` the RAG agent produces a fluent, wrong, and
   confident answer. Agents consuming its output downstream would have no
   signal that the retrieval was a miss.
3. **N=10 is small.** Category-level cells have n≤3. We interpret the
   per-category numbers as qualitative evidence for where each paradigm
   breaks, not as precise estimates. The `generate-eval` harness can produce a
   larger auto-generated set; with 10 hand-verified questions we prioritised
   gold-answer correctness over volume.

## 5. Conclusion

Holding extraction *effort* constant — both sides fully automated from the
same Markdown — a text-to-Cypher graph agent substantially outperforms a
chunk-RAG agent on questions requiring composition, counting, or
enumeration, with no latency penalty and comparable 1-hop performance. The
graph agent's failure modes are either extraction misses (facts absent from
the KGGen output) or Cypher-authoring mistakes on transitive / negated
patterns; the RAG agent's failure modes are semantically-plausible
confabulations on multi-hop joins and aggregations. For workflows where such
joins dominate — enterprise knowledge, architectural Q&A, policy — automated
graph-RAG is a viable default, provided the extractor's recall on the
target corpus is acceptable.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy, C.,
  Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting Knowledge Graphs
  from Plain Text with Language Models*. arXiv:2502.09956.
- LangGraph. <https://langchain-ai.github.io/langgraph/>.
- Neo4j. <https://neo4j.com/docs/>.
- Chroma. <https://docs.trychroma.com/>.
