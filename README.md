# graph-rag-graph-agent

A controlled experiment comparing two LangGraph agents over the same
raw Markdown corpus, each ingested via a fully automated pipeline:

- **RAG agent** — OpenAI LLM + a `search_wiki` tool backed by a Chroma
  vector index built from Markdown in `$KNOWLEDGE_DIR`.
- **Graph agent** — OpenAI LLM + a text-to-Cypher `run_cypher` tool
  backed by a Neo4j graph. The graph itself (`graph.cypher`) is
  extracted from the same Markdown by
  [KGGen (Mo et al., 2025)](https://arxiv.org/abs/2502.09956) — no
  human curation in the middle.

Both agents share a session scratchpad (`scratchpad_read/write/clear`) for
multi-step reasoning and are wrapped in a LangGraph `MemorySaver` so
conversation history is preserved inside a chat thread.

The eval harness samples the graph, LLM-synthesises a question set across
seven categories designed to surface graph-RAG strengths, then grades both
agents with an LLM judge.

This setup compares two **automated** ingestion paradigms head-to-head:
`markdown → chunks → vectors → semantic retrieval` vs.
`markdown → KGGen → Cypher → graph traversal`. Any difference in agent
accuracy therefore reflects the *combined* effect of (a) extraction
quality and (b) reasoning strategy over the extracted representation —
not a hand-idealised graph advantaging one side.

## Experimental integrity

This repo is a scientific comparison, not a demo. To keep the comparison
fair:

- **The agents are 100% domain-agnostic.** Neither `rag_agent.py` nor
  `graph_agent.py` contains any entity names, relationship-type names, or
  other facts from a specific corpus. Both agents learn the vocabulary at
  runtime (the graph agent is given a live schema dump; the RAG agent
  learns from what `search_wiki` returns). Few-shots use placeholders like
  `<SUBJECT>` / `<REL_TYPE>`.
- **Symmetric prompt scaffolding.** Both agents get a persona + retrieval
  strategy + placeholder examples of the same shape, and both share the
  same answer-shape contract (count + names together, enumerate negations,
  cover every asked-for attribute). Any guidance added to one should have
  a mirror in the other.
- **Paradigm-native discovery, mirrored in spirit.** RAG has `search_wiki`
  for chunk-level semantic discovery; the graph agent has `neighbourhood`
  (how an entity actually connects) and `resolve_entity` (fuzzy name
  matching). Neither agent gets a capability the other's paradigm would
  also benefit from.
- **Schema-grounded guardrails, not hand-curated vocabulary.** The graph
  agent's `run_cypher` pre-flights every query: rel types or property
  keys not in the live schema surface as "did you mean X, Y, Z" NOTEs
  derived from `difflib` over the schema at runtime — no hardcoded
  synonym list. The corresponding fairness move for RAG is to lean on
  its native retriever scoring.
- **Shape-based eval filters.** The question generator drops slug-shaped
  (`team-platform`) and env-var-shaped (`DB_HOST`) entities using regexes,
  not a per-domain allow-list.
- **Rel-type-agnostic samplers.** Negation and dependency-chain samplers
  use `-->` / `-[*..]->` rather than hardcoding which edges "count".
- **Gold sets live outside the package** (`eval_data/*.yaml`), never
  embedded in agent or eval code.
- **No hand-curation asymmetry at the ingestion step.** RAG gets
  automated chunking + embedding; the graph is produced by KGGen from
  the same Markdown, not hand-authored. This means the graph agent is
  bounded above by KGGen's extraction recall — a fact that's *in* the
  Markdown but *not* in the extracted graph is unreachable for it. We
  accept that as a real trade-off of the paradigm rather than
  "patching" the graph, because patching would leak human curation
  into only one side of the comparison.

If you iterate on agent prompts using this repo's eval results, you're
overfitting to your test set — pick a different question set, or ideally a
different corpus, to validate changes.

### Diagnosing graph-agent misses

Because the graph is KGGen-extracted, a graph miss is either:

- **extraction miss** — the fact isn't in the graph at all (KGGen
  didn't capture that edge or entity); not tunable by changing the
  agent.
- **reasoning miss** — the fact *is* in the graph, but the agent
  didn't construct the right Cypher; tunable.

When analysing a failing question, run the "oracle" Cypher you'd write
by hand against the graph. Empty → extraction miss. Non-empty → work
on the agent.

## Prerequisites

- Python 3.14 (see `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) — all package management
- A running Neo4j instance reachable from your machine
- An OpenAI API key

## Setup

```bash
uv sync
cp .env.example .env   # fill in OPENAI_API_KEY and NEO4J_*
```

## Pointing at a new corpus

No code edits required — everything configurable via env vars in `.env`:

| Var | Default | Purpose |
|---|---|---|
| `KNOWLEDGE_DIR` | `./knowledge_sources` | Directory of Markdown files for RAG ingestion |
| `GRAPH_CYPHER_PATH` | `$KNOWLEDGE_DIR/graph.cypher` | Cypher file loaded into Neo4j |
| `CHROMA_DIR` | `./.chroma` | Where to persist the vector store |
| `CHROMA_COLLECTION` | `knowledge-corpus` | Collection name |
| `DOMAIN_DESCRIPTION` | *(unset)* | One-line flavor injected symmetrically into both agents' persona |
| `EVAL_ENTITY_BLOCKLIST` | *(unset)* | Comma-separated exact names to exclude from question seeds |

## Workflow

```bash
# 1. Build the vector index (writes to $CHROMA_DIR)
uv run python main.py ingest-rag

# 2. Load the graph into Neo4j (wipes the DB by default, re-run is safe)
uv run python main.py load-graph

# 3. Generate the eval set (samples the graph, LLM-synthesises questions)
uv run python main.py generate-eval --n 25
#    -> writes graph_rag_graph_agent/eval/questions.yaml; review by hand

# 4. Run both agents and produce a markdown report
uv run python main.py eval
#    -> eval_runs/<run_id>.json + eval_report.md

# Run against a hand-curated gold set instead of the auto-generated one
uv run python main.py eval -q eval_data/shopflow_gold.yaml

# To promote a run + paper into a versioned snapshot for Git, see
# "Iteration snapshots" below (new-iteration).

# Spot-check either agent interactively
uv run python main.py chat --agent rag
uv run python main.py chat --agent graph
```

## Iteration snapshots (paper + eval)

Experiment runs produce **scratch** artifacts under `eval_runs/<run_id>.json` and
a rendered root `eval_report.md` (see `.gitignore` — not meant as the
long-lived source of truth). For anything you want in **version control** as a
citable “this is the run behind the paper,” use **versioned iteration
folders** and the `new-iteration` command.

### Layout

```text
iterations/
  v1/
    iteration.yaml   # id, parent, run_id, question_count, summary, changes[]
    paper.md         # paper text for that iteration
    eval_report.md   # rendered report for that run
    eval_run.json    # copy of eval_runs/<run_id>.json at cut time
  v2/   ...
  latest -> vN       # symlink to the newest iteration
paper.md              # at repo root: copy of iterations/latest/paper.md
                      # (kept in sync by new-iteration; prefer not to edit
                      # root paper.md without a matching iteration cut)
```

- **`eval_runs/*.json`** — append-only local log, **gitignored** (avoids merge
  noise; exploratory runs are fine).
- **`iterations/v*/`** — **tracked** when you commit: the frozen run + report +
  paper for that version.

### Cutting a new iteration

1. **Prerequisites:** Chroma and Neo4j match the corpus you are evaluating; `.env`
   has `OPENAI_API_KEY` and Neo4j settings. Neo4j must be reachable (the graph
   side of the eval will fail otherwise).
2. **Run the eval** from the **project root**, then copy the **run id** from the
   printed `Raw results: .../eval_runs/<run_id>.json` line — the id must match
   that file exactly.
   ```bash
   uv run python main.py eval -q eval_data/shopflow_gold.yaml
   ```
3. **Update the paper** for the *next* version: read `eval_report.md` and carry
   through overall scores, the category table, mean/p95 latency, and
   discussion — figures in `paper.md` should match the run, not a prior run. Add
   a `## Changelog (vN)` at the top (one bullet per change, similar to
   `iteration.yaml`’s `changes` list) and keep claims within the study’s
   design (e.g. asymmetric RAG vs. graph ReAct limits are intentional). Save the
   draft to **repo root** `paper.md` (or another path you pass in the next
   step).
4. **Freeze the iteration** with the next `vN` id (do not create
   `iterations/vN/` by hand; `new-iteration` creates the directory and
   `latest`). Refuses if that folder already exists.
   ```bash
   uv run python main.py new-iteration --id v3 --run-id <run_id> --parent v2 \
     --from-paper paper.md \
     --summary "One-line description of v3" \
     --change "file or area: what changed" \
     --change "Another bullet"
   ```
   - **`--from-paper paper.md`** — use when the draft to snapshot is the root
     `paper.md`. If you omit it, the default source is the **parent
     iteration’s** `paper.md`, which is easy to misuse after editing the root
     file.
   - **`--parent`** — previous version (e.g. `v2`); if omitted, the CLI uses
     `iterations/latest`’s target when present.
5. The command copies `paper.md` into `iterations/<id>/`, writes
   `eval_run.json` + `eval_report.md` + `iteration.yaml`, repoints
   `iterations/latest` → `<id>`, and copies the iteration’s `paper.md` back to
   the root so the repo shows the current paper.
6. **Commit** `iterations/<id>/`, `paper.md`, and any code or data changes in one
   logical commit.

If you no longer need a scratch `eval_runs/<run_id>.json` for local debugging, you
can delete it after the cut — the citable copy lives under
`iterations/<id>/eval_run.json`.

Run `uv run python main.py new-iteration --help` for the full option list.

## Question categories

`generate-eval` draws from seven categories chosen to expose where chunk
retrieval typically struggles:

| Category | What it tests |
| --- | --- |
| `one_hop` | baseline single-edge facts |
| `multi_hop_2` | two-hop joins |
| `multi_hop_3` | three-hop joins |
| `dependency_chain` | transitive reachability (any relationship types) |
| `shared_neighbor` | intersection between two entities' neighborhoods |
| `aggregation_count` | counts over a relation |
| `negation` | "which X do NOT …" |

The report (`eval_report.md`) aggregates mean judge score per category per
agent, plus latency and a per-question breakdown.

## Project layout

```
graph_rag_graph_agent/
  config.py              env + path config
  agents/
    rag_agent.py         chunk-RAG React agent
    graph_agent.py       text-to-Cypher React agent
    memory.py            scratchpad tools
    common.py            shared persona / prompt helpers
  rag/
    ingest.py            markdown -> chunks -> Chroma
    retriever.py         WikiRetriever
  graph/
    driver.py            cached neo4j driver
    loader.py            run graph.cypher into Neo4j
    schema.py            introspect schema for the prompt
    tools.py             run_cypher (read-only + schema preflight),
                         list_relationship_types, list_entities_like,
                         find_rel_types_like, resolve_entity, neighbourhood
  eval/
    generate.py          sample graph + LLM-synthesise questions
    questions.yaml       generated question set (review by hand)
    judge.py             LLM-as-judge
    run.py               run both agents + grade + save JSON
    report.py            markdown report
eval_data/               hand-curated gold question sets (one per corpus)
eval_runs/               raw run JSON (gitignored; promoted via new-iteration)
iterations/              versioned paper + eval_report + eval_run.json per cut
knowledge_sources/       default corpus (overridable via KNOWLEDGE_DIR)
paper.md                 landing write-up; mirror of iterations/latest/paper.md
main.py                  typer CLI (eval, new-iteration, …)
```

## Safety notes

- The graph agent's `run_cypher` rejects write keywords (`CREATE`, `MERGE`,
  `DELETE`, `SET`, `REMOVE`, `DROP`, `FOREACH`) before hitting Neo4j.
- Every Cypher query is pre-flighted against the live schema; unknown
  rel types or property keys are surfaced as NOTEs with fuzzy "did you
  mean" suggestions so the agent self-corrects rather than looping.
- Results are truncated to 50 rows per call so the agent can't flood its
  own context with a bad `MATCH (n) RETURN n`.
- **ReAct step caps differ by design:** the RAG agent is hard-capped at **24**
  steps per question; the graph agent is capped at **40** so multi-hop Cypher +
  resolution can finish without hitting the guard rail on harder items.

## Costs

`generate-eval` and `eval` both call OpenAI. Defaults are tuned to be
cheap (`gpt-4o-mini` for agents, `gpt-4o` for the judge,
`text-embedding-3-small` for embeddings). Override via `AGENT_MODEL` /
`JUDGE_MODEL` / `EMBEDDING_MODEL` in `.env`.

## References

- Mo, B., Yu, K., Kazdan, J., Cabezas, J., Mpala, P., Yu, L., Cundy,
  C., Kanatsoulis, C., & Koyejo, S. (2025). *KGGen: Extracting
  Knowledge Graphs from Plain Text with Language Models*.
  arXiv:2502.09956. <https://arxiv.org/abs/2502.09956> —
  the text-to-KG extractor used to produce `graph.cypher` from the
  Markdown corpus.
- [LangGraph](https://langchain-ai.github.io/langgraph/) — ReAct
  agent framework and conversation checkpointing.
- [Neo4j](https://neo4j.com/docs/) — graph database and Cypher query
  language.
- [Chroma](https://docs.trychroma.com/) — vector store used by the
  RAG agent.
