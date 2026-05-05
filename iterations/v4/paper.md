# Automated Chunk-RAG vs. Automated Graph-RAG: A Controlled Comparison over a Shared Markdown Corpus

## Changelog (v4)

- graph/schema.py: schema fetch now embeds every rel-type spelling
  (`text-embedding-3-small`) and runs single-link union-find clustering
  at cosine threshold 0.70. The resulting **concept clusters** (e.g.
  `built on: BUILT_USING|IS_BUILT_WITH|WAS_BUILT_ON`) are surfaced in
  the schema dump so the agent sees pre-computed rel-type unions
  before writing Cypher. Cross-cluster query-time matching uses a
  looser 0.55 threshold so cross-cluster near-synonyms still surface
  on demand (e.g. `DEPENDS_ON ↔ RELIES_ON` cosine 0.589). Embeddings
  are best-effort: schema falls back to the v3 behaviour if the API is
  unavailable.
- graph/tools.py: new **`reach(entity_name, concept, direction, depth)`**
  tool. Embeds the concept phrase, finds every rel-type spelling within
  threshold, and runs the variable-length Cypher with the full union -
  collapsing the v3 "find_rel_types_like + run_cypher" recipe into one
  call. Code-enforced cap of 4 calls per question/thread to prevent the
  loop pathology (see §6).
- graph/tools.py: preflight on `run_cypher` now flags **bare
  variable-length paths** (`[*1..N]` without a rel-type filter) with a
  NOTE pointing at the `reach` tool / a typed union; on a 233-rel-type
  KGGen graph an unfiltered `*` traversal pulls in unrelated
  infrastructure and produces noise.
- agents/graph_agent.py: prompt updated to (a) point at the visible
  Concept clusters as the canonical rel-type union source, (b) describe
  `reach` and its narrow applicability (transitive questions only;
  not single-hop attribute lookups; cap of 2 retries before switching
  tactics), (c) add the explicit anti-pattern (gold-019 in v3) of
  ignoring a looked-up rel-type union and substituting different
  spellings.

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

**Abstract (v4).** v4 acts on the v3 diagnostics. Three changes,
paradigm-symmetric to the embedding-based RAG side: (a) **schema-time
concept clusters** - rel-type spellings are embedded and grouped by
cosine, surfaced directly in the prompt so the agent sees
`BUILT_USING|IS_BUILT_WITH|WAS_BUILT_ON` instead of having to discover
the family by ad-hoc tool calls; (b) a **`reach(entity, concept,
direction, depth)`** tool that builds the rel-type union and runs the
variable-length Cypher in one call, fixing the v3 gold-019 failure mode
where the agent looked up the union and then ignored it; (c) a
**preflight NOTE** on bare `[*N..M]` paths. On the same 30-question set,
the v4 graph agent scores **0.70** vs. RAG **0.45** (v3: 0.72 / 0.47),
overall flat within the ±0.25-per-cell n=4 noise floor but with two
clean per-cell wins — `shared_neighbor` 0.88→**1.00** and `multi_hop_2`
0.80→**0.90** — paid for by a corresponding regression on `multi_hop_3`
(1.00→0.75) where mixed-concept hops ("developed by *person*",
"developed in *language*") confuse the embedding-based concept
matcher. Attribution improves from 19/10/1 to **20/9/1**
(agent_ok/agent_miss/extraction_miss). The most informative finding is
behavioural: the agent enthusiastically adopted `reach` (27 of 165
graph tool calls), but uses it as a generic try-this-first tool rather
than only on transitive questions, and a code-enforced 4-call cap was
required after the first attempt deteriorated to 0.53 with the agent
calling `reach` 16+ times in a loop on a single question. Run
metadata: `20260502T135653Z-3202a9`.

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

## 3. Results (v4 run)

### 3.1 Accuracy by category

Per-category means use **n=4** or **n=5** per cell. v4 introduces the
behavioural changes (concept clusters, `reach` tool, bare-`*` preflight);
v3 column is the diagnostic-instrumented re-run of the v2 agent. A
single-verdict flip in an n=4 cell shifts the cell mean by 0.25, so
read per-cell movement against that floor.

| Category            | RAG (v4)   | RAG (v3)   | Graph (v4) | Graph (v3) |
| ------------------- | ---------- | ---------- | ---------- | ---------- |
| `one_hop`           | 0.80 (n=5) | 0.80 (n=5) | 0.80 (n=5) | 0.80 (n=5) |
| `multi_hop_2`       | 0.10 (n=5) | 0.10 (n=5) | **0.90** (n=5) | 0.80 (n=5) |
| `multi_hop_3`       | 0.25 (n=4) | 0.25 (n=4) | 0.75 (n=4) | **1.00** (n=4) |
| `dependency_chain`  | 0.75 (n=4) | 0.75 (n=4) | 0.38 (n=4) | 0.50 (n=4) |
| `shared_neighbor`   | 0.88 (n=4) | 0.88 (n=4) | **1.00** (n=4) | 0.88 (n=4) |
| `aggregation_count` | 0.00 (n=4) | 0.12 (n=4) | 0.50 (n=4) | 0.50 (n=4) |
| `negation`          | 0.38 (n=4) | 0.38 (n=4) | 0.50 (n=4) | **0.50** (n=4) |
| **Overall**         | **0.45**   | **0.47**   | **0.70**   | **0.72**   |

Net per-cell motion (graph): two clean wins (`shared_neighbor +0.12`,
`multi_hop_2 +0.10`), two losses (`multi_hop_3 -0.25`,
`dependency_chain -0.12`), three flat. The overall delta of -0.02 is
within run-to-run noise; the per-cell story is informative — see §7.

### 3.2 Latency

| Agent | mean (s, v4) | p95 (s, v4) | mean (s, v3) | p95 (s, v3) |
| ----- | ------------ | ----------- | ------------ | ----------- |
| RAG   | 9.57         | 21.77       | 10.24        | 18.42       |
| Graph | 9.64         | 28.49       | 8.18         | 20.71       |

The graph agent's v4 mean latency is up ~1.5s vs v3, driven by the
new `reach` tool's variable-length Cypher (slower than the targeted
single-rel-type queries v3 produced) plus a small recursion-cap tail
on the two questions where the agent looped on `reach` past the
in-tool cap (gold-002, gold-016).

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

## 6. v4 levers and outcomes

### 6.1 Concept clusters in the schema dump

Embedding-clustered rel-type families are visible in the prompt before
the agent writes any Cypher. On 233 KGGen rel-type spellings, single-link
union-find at cosine 0.70 yields 35 multi-clusters. The top-volume groups
match the question set's relational vocabulary: `built on:
BUILT_USING|IS_BUILT_WITH|WAS_BUILT_ON`, `develops:
DEVELOPED_IN|DEVELOPS|IS_DEVELOPED_AS|IS_DEVELOPED_BY|IS_DEVELOPED_IN`,
`implements: IMPLEMENTED|IMPLEMENTED_IN|IMPLEMENTS|IS_IMPLEMENTED_BY|...`,
and 32 others. A few stubborn pairs that the gold set cares about
(`DEPENDS_ON ↔ RELIES_ON`, cosine 0.589) sit just below the cluster
threshold; they remain singletons in the prompt but are paired at
query time by the looser 0.55 threshold of `union_for_concept`.

### 6.2 `reach` tool: heavy adoption, tactical mis-use

The agent took to `reach` immediately: 27 of 165 graph tool calls
across the 30 questions (16%). Use is concentrated in
`dependency_chain` (11 calls), `multi_hop_3` (6), `multi_hop_2` (5).
This produced the clean per-cell wins on `multi_hop_2` and
`shared_neighbor`. It also produced two failure modes:

1. **Cap-and-loop.** The first v4 attempt scored 0.53 (down from 0.72).
   Trace forensics: on gold-005 ("who authored the QuickCart ADR?")
   the agent called `reach` 16 times, cycling through different
   concept words on the same wrongly-resolved entity, exhausting the
   step budget. The prompt rule "use `reach` at most twice" was
   ignored. The fix was code-enforced: a per-thread cap of 4
   `reach` calls; on the 5th the tool returns an error pointing
   at `list_entities_like` and `neighbourhood`. With the cap the
   second v4 attempt hit 0.67; the third (with a tighter prompt
   delineating when **not** to use `reach`) hit 0.70.

2. **Mixed-concept hops.** Variable-length `reach` is wrong for
   3-hop chains where each hop is a different relation
   ("person *developed* service *developed_in* language") — the
   embedding for "developed" returns both the person→service and the
   service→language families, and the variable-length traversal
   cannot disambiguate. This is mechanically the same failure mode
   the v3 paper called out for `gold-016`, now expressed as the
   agent reaching for `reach` instead of decomposing. Net effect:
   `multi_hop_3` regressed 1.00→0.75.

### 6.3 Bare `[*N..M]` preflight

The new NOTE on unfiltered variable-length patterns fired zero times
in this run — the agent never wrote a bare `*` query, even on the
questions where v3 traces showed it considered it. Difficult to
attribute: the prompt now mentions the concept clusters and the
`reach` tool, both of which obviate the bare `*` shortcut. The
preflight is a cheap insurance policy more than an active lever.

### 6.4 Failure attribution shift

Across n=30 graph rows: **20 agent_ok, 9 agent_miss, 1
extraction_miss** (v3: 19/10/1). The single `extraction_miss` is
still `gold-002`. Movement is concentrated in `multi_hop_2` (3→4
agent_ok) and `shared_neighbor` (3→4), offset by `multi_hop_3`
(4→3) and `dependency_chain` (1→1, but the agent_miss on
`gold-019` now traces to the alias-mismatch failure mode rather
than the rel-type-substitution failure mode v3 documented).

### 6.5 What v5 should change

* **Alias-aware entity resolution.** Two of v4's regressions
  (gold-016, gold-019) trace to the agent picking a snake-case
  entity name (`data_lineage_service`, `service-payments-service`)
  that has fewer outgoing edges than its title-case counterpart
  (`Data Lineage Service`, `Payments Service`). `resolve_entity`
  should return both forms, or `reach` should silently union over
  alias-matched names.
* **Tighter `reach` invocation.** The 4-call cap is a band-aid; a
  better signal would be "after `reach` returns 0 matches, prefer
  `neighbourhood` over a different concept word" - this was in the
  prompt but not heeded. Possibly enforce by returning a stronger
  error message after the *first* zero-match `reach` rather than
  the fifth.
* **Decomposition over reach for mixed-concept multi-hop.** The
  3-hop few-shot already exists; v5 could lift the `multi_hop_3`
  cell back to v3's 1.00 by routing it through scratchpad-bridged
  Cypher rather than letting the agent default to `reach`.

## 7. Conclusion

Holding extraction *effort* constant — both sides fully automated from
the same Markdown — a text-to-Cypher graph agent still outperforms
chunk-RAG on this benchmark overall (0.70 vs. 0.45 in v4), with the
advantage visible on multi-hop structure and shared-neighbour queries,
while **negation remains difficult for both** under automated
extraction. v4 acts on the v3 diagnostics: schema-time concept
clusters, an embedding-driven `reach` tool, and a preflight
bare-`*` warning. The overall score is statistically flat vs v3
(0.70 vs 0.72; ±0.25/cell noise floor on n=4) but the per-cell
profile is informative — `shared_neighbor` and `multi_hop_2` clean up,
`multi_hop_3` regresses on mixed-concept hops the new tool can't
disambiguate. The behavioural lesson is sharper than the score: an
LLM agent will adopt a new tool enthusiastically and use it well
beyond its design scope, requiring a code-enforced cap to avoid
loop pathologies. v3 attribution moves from 19/10/1 to 20/9/1, and
the diagnostic split now lets v5 work pull at the alias-resolution
and decomposition levers above without re-running the analysis.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy, C.,
  Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting Knowledge Graphs
  from Plain Text with Language Models*. arXiv:2502.09956.
- LangGraph. <https://langchain-ai.github.io/langgraph/>.
- Neo4j. <https://neo4j.com/docs/>.
- Chroma. <https://docs.trychroma.com/>.
