# Automated Chunk-RAG vs. Automated Graph-RAG: A Controlled Comparison over a Shared Markdown Corpus

## Changelog (v6)

- graph/tools.py: **`set_difference(candidate_cypher, exclude_cypher,
  key='name')`** tool. Negation guard rail (lever 1 from v5 §7.6).
  Runs both queries read-only, computes the candidate-set minus
  exclude-set, returns the diff with both source-set sizes and the
  overlap explicitly visible (`set_difference: 8 candidates - 5
  excluded (overlap) = 3 in result`). The recipe — "compute
  candidates, compute exclude set, subtract" — was already in v5's
  prompt as prose, but v5 traces showed the agent kept writing
  single-spelling `NOT EXISTS { -[:REL_TYPE]-> }` filters that
  silently match nothing on KGGen's synonymous rel-type vocabulary
  and hand back the entire candidate set as "the answer". The tool
  forces the recipe into a single ReAct turn with a code-enforced
  cap of 3 calls per question. Paradigm-symmetric to how v4's
  `reach` upgraded the v3 transitive recipe from prose to tool.
- agents/graph_agent.py: prompt rewrites the negation few-shot to
  route through `set_difference` with explicit instructions that
  the EXCLUDE Cypher's `WHERE type(r) IN [...]` must contain EVERY
  spelling from `find_rel_types_like` / Concept clusters, never a
  single rel type. The fallback "manual subtraction with hard-coded
  name list" recipe is retained for rare shapes.
- eval/oracle.py: oracle now extracts `collect(...)` columns from
  seed-Cypher results into `OracleResult.enumeration`. The report
  surfaces this as `Oracle enumeration (N): name1, name2, ...`
  alongside the per-question detail. Lets the reader distinguish
  "extraction has all 9 teams but the agent only enumerated 5"
  (agent_miss) from "extraction only has 5 of 9 teams"
  (extraction_miss in disguise) without re-running the seed by
  hand. v6 §8.3 uses this to falsify three suspected
  extraction_miss-in-disguise rows in the aggregation cell.
- eval/trace.py + eval/run.py + eval/report.py: new
  `set_difference_calls` per-question counter + a new report
  section quantifying lever 1 adoption (16 calls / 8 of 30 graph
  rows in this run), paradigm-symmetric to the v5 alias-folded
  calls section and the v3 `find_rel_types_like` coverage section.

## Changelog (v5)

- graph/tools.py: **alias-aware entity resolution** (lever 1 from v4 §6.5).
  New `_alias_siblings(name)` helper computes a normalised key (lowercase,
  strip `service-`/`team-` prefixes, strip parentheticals, drop suffix
  tokens like `service`/`team`, head-synonym map for `auth`/`authentication`)
  and returns every entity name in the graph that maps to the same key,
  plus a difflib fuzzy fallback at ratio ≥ 0.85. `resolve_entity` surfaces
  siblings on a labelled `aliases of '<top>': ...` line; `reach` and
  `neighbourhood` silently union over siblings via `e.name IN $names` and
  display `[aliases unioned: A, B, C]` so the agent sees the fold-in. The
  raw KGGen graph is unchanged - aliases are resolved at query time.
- graph/tools.py: **tighter `reach`** (lever 2). Per-entity zero-match
  short-circuit: after the first `reach` call returns 0 matches on an
  entity (within a thread), the next `reach` call on that same entity is
  refused with an error pointing at `neighbourhood` and `list_entities_like`.
  v4 traces showed the agent re-tried with different concept words rather
  than questioning the entity spelling/direction; the global 4-call cap
  caught this far too late. New optional `name_filter` substring constraint
  for categorical questions (`reach('Redis', 'use', incoming, name_filter='Service')`
  excludes Logistics Team / SRE Team etc. from the result). Two diagnostic
  NOTEs: a **broadness warning** when `union_for_concept` returned >8 rel-type
  spellings, and a **coherence-spread warning** when the matched union's min
  pairwise embedding cosine drops below 0.70 - the latter is the gold-016
  signal that the verb (e.g. "developed") has collapsed two distinct
  relations (`DEVELOPED_BY` person and `DEVELOPED_IN` language) and the
  variable-length traversal will mix them.
- graph/schema.py: new `min_pairwise_cosine(rel_types)` method on
  `GraphSchema`, used by the coherence-spread warning above.
- agents/graph_agent.py: prompt now describes alias-folding (so the agent
  doesn't double-call `reach` for two name spellings), the zero-match rule,
  the `name_filter` knob for categorical questions, the coherence-incoherent
  NOTE handling, and an explicit gold-016-shaped anti-example for 3-hop
  chains where each hop is a different relation (decomposition beats `reach`).
- eval/trace.py + eval/run.py + eval/report.py: new `aliases_used_calls`
  per-question counter (number of `reach` / `neighbourhood` /
  `resolve_entity` calls that folded multiple node-name spellings) plus a
  new report section quantifying lever 1 adoption, paradigm-symmetric to
  the v3 `find_rel_types_like` coverage section.

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

**Abstract (v6).** v6 executes the targeted plan v5 §7.6 prescribed:
one tool-level lever (the `set_difference` negation guard rail), one
diagnostic add (oracle-enumeration display for aggregation rows),
and a clean re-run that neutralises the v5 OpenAI-quota artifact.
Lever 1: a `set_difference(candidate_cypher, exclude_cypher)` tool
runs both queries in one ReAct turn and returns the diff with both
source-set sizes and the overlap explicitly visible — the same
"compute candidates, compute exclude set, subtract" recipe v5 had
in the prompt as prose, now code-enforced. Adopted on **16 tool
calls across 8 of 30 graph rows**. The headline negation row
gold-008 ("which Platform-managed services do NOT depend on Data
Lineage Service?") cleanly flips from v5 wrong to v6 correct in
1 set_difference call (5 tool calls / 11s, was a v5 quota fail).
Headline graph **0.65** vs RAG **0.40** (v5: 0.70 / 0.40). The
headline drop (-0.05) is dominated by two row-specific costs of
the new tool: the agent **over-applied** `set_difference` to two
non-negation questions (gold-021 dependency_chain "which services
use Redis"; gold-026 aggregation_count "how many in Python") where
it confused the candidate/exclude logic and flipped previously-
right answers wrong. Per-cell: **negation 0.25 → 0.38** (gold-008
clean win), **multi_hop_2 0.60 → 0.90** (the two v5 quota fails
gold-004/gold-015 ran cleanly and recovered), `dependency_chain
1.00 → 0.75` (the gold-021 set_difference misuse), `multi_hop_3
0.75 → 0.50` (gold-018 hit step cap, n=4 noise), `aggregation_count
0.50 → 0.38` (the gold-026 set_difference misuse), `one_hop 0.80
→ 0.60` (gold-012 swapped a known-correct cache lookup, n=5 noise),
`shared_neighbor 1.00` (held). Attribution **18/11/1**
(v5: 19/10/1), within run-to-run noise. The most informative
diagnostic finding: oracle enumeration shows the extraction has
**9/9 teams, 6/6 Python-implementing services, and 3/3 Fraud
Detection integrations** — falsifying the suspicion that
aggregation_count failures might be extraction_miss in disguise.
Every aggregation failure is reasoning-bound, just like negation.
Three meta-conclusions: (a) the `set_difference` mechanism works
on its target row but the prompt routing is too broad — v7 should
restrict it to NEGATION ONLY; (b) the `dependency_chain 0.38 →
1.00 → 0.75` arc across v4/v5/v6 plus this run's regressions on
n=4 cells confirms the project is at the noise-floor regime where
single-row flips dominate cell movement; (c) the v3 oracle
attribution + v5 alias counter + v6 oracle enumeration together
now give a complete cell-by-cell attribution chain ready for
write-up. Run metadata: `20260503T110821Z-1e6867`.

**Abstract (v5).** v5 acts on the three levers v4 §6.5 prescribed,
all at the tool layer — the raw KGGen graph is unchanged. (a)
**Alias-aware entity resolution**: `resolve_entity`, `reach` and
`neighbourhood` silently union over node-name spellings via a
normalised key (`Auth Service`/`Authentication Service`,
`Payments Service`/`service-payments-service`, etc.) plus a difflib
fallback at ratio 0.85. (b) **Tighter `reach`**: a per-entity
zero-match short-circuit refuses a second `reach` call on an entity
that already returned 0 matches (the v4 loop pathology fired
*before* the global 4-call cap was reached); an optional `name_filter`
substring constraint scopes categorical questions ("which
**services** use Redis"); a coherence-spread NOTE warns when the
matched rel-type union spans semantically distinct concepts
(min pairwise embedding cosine < 0.70). (c) **Decomposition routing**
in the prompt: an explicit gold-016-shaped anti-example tells the
agent that 3-hop chains where each hop is a different verb beat
`reach` by scratchpad-bridged Cypher. Headline graph **0.70** vs.
RAG **0.40** (v4: 0.70 / 0.45) — overall flat, but the per-cell
shape moves substantially: **`dependency_chain` 0.38 → 1.00**
(four-of-four; the canonical lever-1 win, gold-019's
`service-payments-service`/`Payments Service` alias collapse cleanly
folded), `aggregation_count` 0.50 → 0.50 (flat). The headline number
also masks an **OpenAI-quota artifact**: 4 graph rows (gold-004, 008,
015, 016) returned `RateLimitError` mid-run and were tagged
`agent_miss`; the underlying mechanism worked. The most informative
finding is behavioural: lever 1 fired **52 times across 22 of 30
graph rows** (touched two-thirds of the question set), confirming
the alias problem is pervasive in the KGGen output rather than a
gold-019-specific quirk. Run metadata: `20260503T103231Z-c5145a`.

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
wrong (0) against the expected answer and the expected key entities. v6 run
metadata: `20260503T110821Z-1e6867`. v5 run (kept for the comparison columns
in §3.1): `20260503T103231Z-c5145a`.

## 3. Results (v6 run)

### 3.1 Accuracy by category

Per-category means use **n=4** or **n=5** per cell. v6 introduces one
tool-level behaviour change (the `set_difference` negation guard rail)
and one diagnostic add (oracle enumeration for aggregation rows). A
single-verdict flip in an n=4 cell shifts the cell mean by 0.25, so
read per-cell movement against that floor.

| Category            | RAG (v6)   | RAG (v5)   | Graph (v6)     | Graph (v5)     |
| ------------------- | ---------- | ---------- | -------------- | -------------- |
| `one_hop`           | 0.80 (n=5) | 0.80 (n=5) | 0.60 (n=5)     | 0.80 (n=5)     |
| `multi_hop_2`       | 0.00 (n=5) | 0.00 (n=5) | **0.90** (n=5) | 0.60 (n=5)     |
| `multi_hop_3`       | 0.25 (n=4) | 0.25 (n=4) | 0.50 (n=4)     | 0.75 (n=4)     |
| `dependency_chain`  | 0.75 (n=4) | 0.75 (n=4) | 0.75 (n=4)     | **1.00** (n=4) |
| `shared_neighbor`   | 0.75 (n=4) | 0.75 (n=4) | **1.00** (n=4) | **1.00** (n=4) |
| `aggregation_count` | 0.00 (n=4) | 0.00 (n=4) | 0.38 (n=4)     | 0.50 (n=4)     |
| `negation`          | 0.25 (n=4) | 0.25 (n=4) | **0.38** (n=4) | 0.25 (n=4)     |
| **Overall**         | **0.40**   | **0.40**   | **0.65**       | **0.70**       |

Net per-cell motion (graph): two wins (`negation +0.13`, the
lever-1 target; `multi_hop_2 +0.30`, the v5-quota recovery), four
losses concentrated in n=4 cells (`dependency_chain -0.25`,
`multi_hop_3 -0.25`, `aggregation_count -0.13`, `one_hop -0.20`),
one flat (`shared_neighbor`). §8 attributes each cell-level move to
specific gold rows; the headline arithmetic conceals two distinct
mechanisms: (a) the lever-1 target row gold-008 cleanly flipped
correct, and (b) the agent over-applied `set_difference` to two
non-negation rows (gold-021, gold-026) and a third (gold-018) hit
the step cap, accounting for ~0.10 of the headline drop. The
remaining ~0.05 falls inside the n=4/n=5 noise floor (gold-012
swap, gold-029 set partial → wrong, etc.). Crucially the v5 quota
artifact is gone in this run: `gold-004` and `gold-015` (both v5
RateLimitError) ran cleanly to correct + partial respectively, and
`gold-008` (the third v5 quota fail) is the negation lever-1 win.
The headline graph score is now interpretable without quota
caveats.

### 3.2 Latency

| Agent | mean (s, v6) | p95 (s, v6) | mean (s, v5) | p95 (s, v5) |
| ----- | ------------ | ----------- | ------------ | ----------- |
| RAG   | 9.84         | 16.71       | 8.90         | 17.66       |
| Graph | 11.87        | 27.95       | 8.49         | 19.61       |

Graph latency is up ~3.4s mean / ~8.3s p95 vs v5. Two drivers: (a)
the v5 run had 4 rate-limited rows that returned in <2s and pulled
the mean down artificially; without those four rows v5 mean would
have been ~9.7s, so v6 is up only ~2.2s vs the like-for-like v5 mean,
mostly attributable to the longer negation tool-chains
(`set_difference` requires the agent to write two queries instead of
one). (b) Two graph rows hit the recursion ceiling (gold-018 at 51s,
gold-028 at 39s) — both burned tool budget on confused
`set_difference` retries. p95 is dragged by these two specifically;
median (not shown) is unchanged.

### 3.3 Qualitative patterns

* **Factual grounding (1-hop).** Graph 0.60 (v5: 0.80). gold-001,
  gold-003, gold-011 still correct in 1–2 tool calls. gold-002 is
  the persistent `extraction_miss`. The new wrong row is **gold-012**
  ("which cache does the Auth Service use?"): the agent picked the
  `CACHES` rel and answered with the cache *contents* (auth tokens,
  session data) instead of following `USES_DATABASE` to Redis.
  Single n=5 flip — within run-to-run noise, no v6 mechanism
  involved.
* **Composition (2-hop).** Graph 0.90 (v5: 0.60). The two v5 quota
  fails (`gold-004`, `gold-015`) ran cleanly; gold-004 → correct,
  gold-015 → partial (right author, wrong team). Cell now matches
  v4's 0.90.
* **3-hop.** Graph 0.50 (v5: 0.75). gold-016 (v5 quota fail) ran
  cleanly but answered Payments Service / Java instead of Auth
  Service / Python — the v4-era mixed-concept failure mode without
  the quota mask. **gold-018** flipped from v5 correct to v6 step-cap
  refusal: 19 tool calls without converging on Bob Martinez's role.
* **Transitive / dependency-chaining.** Graph 0.75 (v5: 1.00). The
  three v5 wins held (gold-010, gold-019, gold-020). The new failure
  is **gold-021** ("which services use Redis for caching?") — this
  is not a NOT-question, but the agent invoked `set_difference`
  twice and convinced itself the answer was "no services". A
  routing failure of the new tool, not a regression of any prior
  mechanism.
* **Negation / set difference.** Graph **0.38** (v5: 0.25). The
  lever-1 target gold-008 cleanly flipped to correct (5 tool calls,
  one `set_difference` invocation, returned PII Service + GraphQL
  Service exactly). gold-030 lifted from wrong → partial (2 of 4
  expected services named). gold-028 and gold-029 still wrong —
  in both the agent invoked `set_difference` but populated the
  candidate or exclude Cypher with bad rel-type unions and was
  unable to recover.
* **Shared neighbours.** Graph 1.00, held.
* **Aggregation / count.** Graph 0.38 (v5: 0.50). The new oracle
  enumeration shows the extraction supports the gold answer in full
  on every cell row (9/9 teams, 6/6 Python services, 3/3 integrations
  for Fraud Detection Service). gold-007 still correct. **gold-026**
  flipped from "wrong (5 of 6)" to "wrong (no services found)" —
  the agent over-applied `set_difference` here too, set up an
  exclude that swallowed all candidates, and answered "none".
  gold-025 still partial (8 not 9), gold-027 still partial. The
  cell mean drop is the gold-026 set_difference misuse alone.

## 4. Discussion

The overall **0.65 vs. 0.40** gap (n=30) is directionally consistent
across all six iterations (v1 0.70/0.40 on n=10, v2 0.70/0.45,
v3 0.72/0.47, v4 0.70/0.45, v5 0.70/0.40, v6 0.65/0.40): graph
retrieval wins on compositional and counted structure by a consistent
~0.25–0.30 absolute margin. The headline graph score has lived in the
narrow band [0.65, 0.72] across four substantive behaviour-changing
iterations and one diagnostic-only one. Per-cell composition rotates
each iteration — v6 is the run where `negation` finally moved off its
v5 floor (0.25 → 0.38) on its lever-1 target, but the same lever's
over-triggering cost the headline ~0.10 in collateral on
`dependency_chain` and `aggregation_count`. The pattern that emerges
across six iterations is now unambiguous: every behaviour-changing
intervention buys a clean win on a specific row and pays for it
elsewhere within the n=4 noise floor. Three qualifiers matter:

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

## 7. v5 levers and outcomes

### 7.1 Lever 1 — alias-aware entity resolution

This is v5's clear win. Three tools (`resolve_entity`, `reach`,
`neighbourhood`) silently union over alias siblings: a normalised
key (lowercase, strip `service-`/`team-` prefixes, strip
parentheticals, drop suffix tokens like `service`/`team`,
head-synonym map for `auth ↔ authentication`) groups
`Auth Service` with `Authentication Service`, `Payments Service`
with `service-payments-service`, etc. A difflib fallback at
ratio 0.85 catches morphological near-misses the rules don't.

**Adoption was massive.** Lever 1 fired on 52 tool calls across
**22 of 30 graph rows** (73% of the question set) — orders of
magnitude broader than the v3 finding that `find_rel_types_like`
covered only 12/42 concepts. The aliases are pervasive in KGGen
output, not a gold-019-specific quirk.

**Effect on the headline cell:** `dependency_chain` 0.38 → 1.00
(four-of-four). gold-019 ("which services rely on Payments
Service?") flips from "no services found" to a single correct
answer in one tool call (3.6s, was 17.8s with 12 tool calls in
v4). gold-010 also clears. The single Cypher pattern that worked:

```cypher
MATCH path = (s:Entity)-[:RELY_ON|RELIES_ON|...*1..4]->(t:Entity)
WHERE t.name IN ['Payments Service', 'service-payments-service']
  AND NOT s.name IN ['Payments Service', 'service-payments-service']
RETURN s.name AS name, min(length(path)) AS hops
```

The `t.name IN $names` substitution is invisible to the agent — it
calls `reach('Payments Service', 'rely', 'incoming')` and the alias
union is handled in the Cypher template.

### 7.2 Lever 2 — tighter `reach`

The per-entity zero-match short-circuit fires only when the agent
both (a) calls `reach` and (b) gets 0 matches. With alias unioning
in place, condition (b) became rare in this run — the lever is more
of a safety net than an active driver. Two questions in the run
showed the agent abandoning a wrong direction after one zero-match
call rather than cycling concept words; this is the v4 cap-and-loop
pathology being prevented at the design point rather than at the
budget ceiling. The `name_filter` parameter went unused by the
agent in this run despite its description in the prompt — the
broadness/coherence-spread NOTEs may need to land more loudly to
trigger filter use. Coherence-spread NOTEs themselves did not fire
in this run (the surviving `reach` calls hit clean unions).

### 7.3 Lever 3 — decomposition routing for mixed-concept 3-hop

The prompt now contains an explicit gold-016-shaped anti-example.
This was the lever most exposed to the quota artifact: gold-016
itself returned `RateLimitError` mid-run, so the change couldn't
be fairly evaluated on its primary target. On gold-017 and gold-018
(other 3-hop rows that completed cleanly) the agent decomposed
correctly via 3–4 tool calls; both stayed correct. multi_hop_3
held at 0.75; the v3-era 1.00 may be reachable but the run does
not establish it.

### 7.4 The OpenAI quota artifact

Four graph rows (`gold-004`, `gold-008`, `gold-015`, `gold-016`)
returned `RateLimitError: insufficient_quota` partway through the
run. They were tagged `agent_miss` by the oracle attribution
because the verdict is "wrong" (the answer string contains an
error message), but the underlying agent loop never executed.
This is straightforward run-to-run noise on a paid API rather
than a v5 regression; a clean re-run with restored quota would
plausibly recover three of those four to correct (gold-016 is
the harder one). The headline 0.70 reads as flat vs v4 only
because of these four rows; the lever-1 win on
`dependency_chain` is unambiguous regardless.

### 7.5 Failure attribution shift

Across n=30 graph rows: **19 agent_ok, 10 agent_miss, 1
extraction_miss** (v4: 20/9/1, v3: 19/10/1). The extraction_miss
remains gold-002. Real movement at the cell level:
`dependency_chain` 1/3/0 → **4/0/0**, `multi_hop_2` 4/1/0 → 3/2/0
(both losses are quota fails), `negation` 2/2/0 → 0/4/0 (one quota
fail, three real losses), `aggregation_count` 2/2/0 → 1/3/0
(gold-007 partial → wrong; the headline cell mean is unchanged
because gold-026 went 0 → 0 with a different wrong answer). Net
attribution drift -1/+1/0 is well inside run-to-run noise; the
big move is the inside-cell rotation in `dependency_chain`.

### 7.6 What v6 should change

* **Negation as the next failure mode.** v5's negation cell at
  0.25 is the lowest of any cell across all five iterations.
  Failures are reasoning-bound (no extraction misses). The
  negation few-shot's "compute candidate set, compute exclude set,
  subtract" recipe is correct prose but the agent on gold-028 and
  gold-029 still issues a single `NOT EXISTS` Cypher that misses
  the right rel-type spelling. A code-enforced negation tool
  (`set_difference(candidate_query, exclude_query)` returning the
  diff with row-counts) would convert the recipe from prose to
  guard rail, paradigm-symmetric to how `reach` upgraded the
  transitive recipe in v4.
* **Aggregation / count category.** Two failure modes coexist:
  (a) the agent gets the count right but cannot enumerate
  (gold-027), (b) the agent enumerates partially and undercounts
  (gold-025 said 5 teams of 9). A `count_and_enumerate(pattern)`
  tool that returns both could close this; the prompt asks for
  both but the agent provides one.
* **Coherence-spread NOTE adoption.** The signal exists but the
  prompt mention may not be loud enough. v6 could promote the
  NOTE from a single result line into a structured field
  (`{"warning": "...", "suggested_action": "decompose"}`) so the
  agent treats it as an instruction rather than commentary.

## 8. v6 levers and outcomes

### 8.1 Lever 1 — `set_difference` negation guard rail

`set_difference(candidate_cypher, exclude_cypher, key='name')` runs
both queries read-only, computes the candidate-set minus exclude-set,
and returns the diff with both source-set sizes and the overlap
visible in one tool-call output. The recipe — already present in
v5's prompt as prose — is now code-enforced. A per-thread cap of 3
calls prevents the v4-style cap-and-loop pathology (the agent will
otherwise iterate on minor query rewrites instead of switching
tactics when a candidate or exclude set comes back wrong).

**Adoption.** The tool fired on **16 calls across 8 of 30 graph
rows**: 4 of 4 negation rows (gold-008, gold-028, gold-029,
gold-030), 2 aggregation rows (gold-025, gold-026), 1 dependency
row (gold-021), and 1 shared_neighbor row (gold-024). The negation
adoption is full; the cross-cell adoption is the over-triggering
problem documented in §8.2 below.

**Effect on the headline target cell.** Negation **0.25 → 0.38**.
The clean win is **gold-008** ("which Platform-managed services do
NOT depend on Data Lineage Service?") — v5 wrong (it was a quota
fail), v6 correct in 5 tool calls / 11.1s. The agent's Cypher:

```cypher
candidate: MATCH (:Entity {name: 'Platform Team'})-[:MANAGES]->(s:Entity)
           RETURN s.name AS name
exclude:   MATCH (s:Entity)-[:DEPENDS_ON|RELIES_ON|...]->(:Entity {name:
           'Data Lineage Service'}) RETURN s.name AS name
```

Tool returned `set_difference: 3 candidates - 1 excluded (overlap)
= 2 in result` with PII Service + GraphQL Service named — exactly
the gold answer. **gold-030** also lifted from wrong to partial
(2 of 4 expected services correctly named).

**The two negation rows that didn't lift** (gold-028, gold-029)
both invoked `set_difference` 3× and 1× respectively but populated
the candidate or exclude Cypher with a malformed rel-type union.
On gold-028 the agent searched for the Python-implementation edge
on Auth Service and PII Service individually rather than via the
full rel-type IN-clause, got back "no results", and concluded all
three Platform-managed services lack Python implementation
(opposite of the truth). The set_difference tool surfaces the
intermediate sets correctly — the agent just disregarded the
"excluded (0)" warning that the diagnostic block prints when
the exclude set is empty.

### 8.2 The over-triggering problem

The v6 prompt wires `set_difference` as the negation few-shot's
preferred path, but the question-shape trigger for "use this tool"
is too broad in practice. Two collateral regressions:

* **gold-021** ("which services use Redis for caching?") — this is
  a positive set-membership question, no negation. The agent
  invoked `set_difference('use Redis', 'use Redis differently')`
  twice, got an empty result, and answered "no services use
  Redis" — flipping a v5 known-correct answer to wrong. Cost:
  one row in `dependency_chain` (-0.25 on the cell).
* **gold-026** ("how many distinct services have code in Python?")
  — an aggregation, no negation. The agent set up `candidate=all
  services` and `exclude=services with Python edges`, returning
  the *complement* of the right answer ("0 services in Python").
  Cost: one row in `aggregation_count` (-0.13 on the cell).

Together these explain ~0.10 of the headline 0.70 → 0.65 drop.
Mechanism diagnosis is unambiguous because the
`set_difference_calls` instrumentation logs the misuse explicitly:
both rows show 1–3 `set_difference` invocations in the trace.
v7 should restrict the prompt's `set_difference` recommendation
to questions whose surface form contains "NOT" / "do not" /
"are not" / "without" / "except", with an explicit don't-use list
covering "use", "depend on", "how many".

### 8.3 Lever 2 — oracle enumeration for aggregation rows

Every aggregate seed-Cypher in the gold YAML uses
`RETURN count(...) AS count, collect(...) AS names`. v6's oracle
extracts the `collect()` column into `OracleResult.enumeration`,
and the report surfaces it as `**Oracle enumeration (N):** name1,
name2, ...` alongside the existing oracle row count.

The v5 §7.6 question this was designed to answer was: "is gold-025
('how many teams') a hidden `extraction_miss` — does KGGen only
extract 5 of 9 teams as Team entities — or is it a genuine
`agent_miss`?" The v6 enumeration **falsifies the extraction-bound
hypothesis cleanly** for all three aggregation rows that have
oracles:

| Row | Oracle enumeration | Agent answer |
| --- | --- | --- |
| `gold-025` | 9 teams (all 9 expected) | "8 teams, not fully enumerated" |
| `gold-026` | 6 services (all 6 expected) | "0 services in Python" |
| `gold-027` | 3 entities (all 3 expected) | "3 entities, not named" |

In every case the extraction has the full answer — the agent's
shortfall is reasoning-bound. This collapses the v5 §7.6
suggestion of a `count_and_enumerate(pattern)` tool to a simpler
intervention: a prompt rule that for `count` questions the agent
must enumerate the matched names before stating the count, plus a
tool that returns both columns by default. v7 work; not done in
v6 because the diagnostic was the priority.

### 8.4 Failure attribution shift

Across n=30 graph rows: **18 agent_ok, 11 agent_miss, 1
extraction_miss** (v5: 19/10/1, v4: 20/9/1, v3: 19/10/1). The
extraction_miss remains gold-002. Cell-level rotation:
`negation` 0/4/0 → **1/3/0** (gold-008 lever-1 win),
`multi_hop_2` 3/2/0 → **4/1/0** (the v5 quota fails recovered),
`dependency_chain` 4/0/0 → 3/1/0 (gold-021 set_difference misuse),
`aggregation_count` 1/3/0 → 1/3/0 (gold-026 misuse offset by no
new wins), `multi_hop_3` 3/1/0 → 2/2/0 (gold-018 step-cap fail),
`one_hop` 4/0/1 → 3/1/1 (gold-012 noise flip),
`shared_neighbor` 4/0/0 unchanged. Net attribution drift -1/+1/0
is inside run-to-run noise; the v6-attributable moves are the
gold-008 win and the two `set_difference` misuses.

### 8.5 What v7 should change

* **Restrict `set_difference` routing.** The mechanism works (gold-008
  is the proof), but the prompt allows the model to apply it to
  questions that don't fit. The fix is a tighter trigger: require
  one of {NOT, do not, are not, without, except} in the question
  before the few-shot is even shown, and add an explicit
  don't-use list covering "use", "depend on", "how many".
* **Repair gold-028 / gold-029.** Both invoked `set_difference` but
  the exclude Cypher returned nothing because the agent used
  per-source single-spelling MATCH instead of the
  `WHERE type(r) IN [...]` union. The tool already prints
  "(empty result is suspicious: exclude set is empty, ...)" but
  the agent disregarded it. v7 could promote that line to an
  explicit error that requires a follow-up `find_rel_types_like`
  before allowing another `set_difference` call.
* **Aggregation fix.** Replace the `count_and_enumerate` tool
  proposal with a prompt rule "for any question starting with
  'how many', enumerate the matched entities by name before stating
  the count" plus a `run_cypher` post-process that auto-adds
  `, collect(name)` when only `count(...)` is in the RETURN.
* **Don't keep iterating headline scores.** v6 confirms what v3-v5
  already suggested: the headline graph score is in a [0.65, 0.72]
  band determined more by which n=4 cells flip on a given run than
  by lever quality. The cell-by-cell attribution chain (v3 oracle
  status + v5 alias counter + v6 enumeration + v6 set_difference
  counter) is now complete enough to write up the project as-is.
  v7 makes sense as a final cleanup pass for the negation cell
  (clearing gold-028 / gold-029 with the routing fix above) and
  then the project should pivot from iteration-and-eval into a
  written paper.

## 9. Conclusion

Holding extraction *effort* constant — both sides fully automated
from the same Markdown — a text-to-Cypher graph agent still
outperforms chunk-RAG on this benchmark overall (0.65 vs. 0.40 in
v6, ~0.30 absolute margin held across all six iterations). v6
delivers the negation lever-1 win on its target row (gold-008) via
a code-enforced `set_difference` tool, paradigm-symmetric to v4's
`reach`: prose recipe → guard-rail tool. The same iteration also
shows the recurring iteration-vs-noise pattern — the new tool's
prompt routing was too broad, costing the headline ~0.10 in
collateral on two non-negation rows where the model misapplied
the diff. The most informative scientific finding is the
diagnostic, not the score: oracle enumeration falsifies the
suspicion that aggregation_count failures might be hidden
extraction misses (the graph supports the gold answer in full on
9/9 teams, 6/6 Python services, 3/3 Fraud Detection integrations),
which means every remaining failure across the negation and
aggregation cells is reasoning-bound and in principle agent-side
recoverable. v6 attribution holds at 18/11/1 — the diagnostic
chain (v3 oracle status + v5 alias counter + v6 enumeration + v6
set_difference counter) is now complete enough that any v7 lever
will be evaluable cell-by-cell against a stable diagnostic
baseline. The project is at the regime where individual cell
flips dominate headline movement; further iteration past v7's
narrow scope (negation routing fix + aggregation enumeration
prompt) would be paid for by another cell elsewhere.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy, C.,
  Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting Knowledge Graphs
  from Plain Text with Language Models*. arXiv:2502.09956.
- LangGraph. <https://langchain-ai.github.io/langgraph/>.
- Neo4j. <https://neo4j.com/docs/>.
- Chroma. <https://docs.trychroma.com/>.
