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

This split is **computed automatically** by the eval. Every gold
question carries a `seed_cypher` that the eval runs read-only against
the live graph as an oracle: 0 rows → `extraction_miss`, ≥1 rows
paired with a wrong/partial answer → `agent_miss`, ≥1 rows paired
with a correct answer → `agent_ok`. See "How the eval pipeline
works" below for the full bucket definition and where it surfaces in
the report.

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

# Restrict to one agent (still requires Neo4j up: the oracle Cypher
# runs per-question regardless of which agent set you select)
uv run python main.py eval --agent rag --limit 5

# To promote a run + paper into a versioned snapshot for Git, see
# "Iteration snapshots" below (new-iteration).

# Spot-check either agent interactively
uv run python main.py chat --agent rag
uv run python main.py chat --agent graph
```

## How the eval pipeline works

The `eval` command turns a gold question set into one JSON run file
plus a rendered markdown report. It's the same pipeline whether you
pass `eval_data/shopflow_gold.yaml` or the auto-generated
`graph_rag_graph_agent/eval/questions.yaml`.

### Gold question schema

Each entry in a gold YAML carries:

| Field | Purpose |
|---|---|
| `id` | Stable id (e.g. `gold-001`) used as the join key in reports. |
| `category` | One of the seven categories below; drives the per-category aggregation. |
| `question` | Natural-language prompt sent to both agents. |
| `expected_answer` | Free-text gold answer; fed to the LLM judge. |
| `expected_entities` | Names that must appear in a correct answer; the judge weighs these heavily and the trace extractor uses them to find the first tool output where any showed up. |
| `seed_cypher` | Read-only Cypher whose row count grounds the gold answer in the live graph. Doubles as the **oracle**: 0 rows → graph extraction miss; ≥1 rows → reachable. Empty string means "no oracle for this question" (the fact lives only in the markdown). |
| `seed_description` | Human-readable shape of the gold structure (for reviewers). |
| `concepts_in_question` | English verbs / noun-verb phrases (e.g. `manages`, `depends on`) whose rel-type spellings the graph agent should union via `find_rel_types_like` before answering. The eval scores **coverage** — did the agent actually probe each concept? — without altering agent behaviour. |

The auto-generated set (`generate-eval`) emits the first five fields;
the v3 oracle and coverage fields are added by hand when curating a
gold set.

### Per-question loop

For each `(question, agent)` pair, `run_eval`
(`graph_rag_graph_agent/eval/run.py`) does the following:

1. **Run the oracle once per question** (cached across agents). The
   `seed_cypher` is executed read-only against Neo4j; the row count,
   any error, and a `has_oracle` flag are stored on every turn that
   shares the question id. This is why Neo4j must be reachable even
   for `--agent rag`.
2. **Invoke the agent** via `ask_with_trace`, which returns both the
   final answer and the raw LangGraph message list. Latency is
   measured around this call. Agent errors are captured rather than
   raised, so one broken question doesn't kill the run.
3. **Grade the answer** with the LLM-as-judge
   (`graph_rag_graph_agent/eval/judge.py`, default `gpt-4o`),
   producing a verdict (`correct` / `partial` / `wrong`) and a
   rationale.
4. **Extract a trace** from the message list
   (`graph_rag_graph_agent/eval/trace.py`): tool-call count, every
   `run_cypher` query (with its row count and any preflight NOTEs),
   `find_rel_types_like` arguments, whether the recursion limit
   tripped (detected via the LangGraph "Sorry, need more steps…"
   marker), and the step index at which any `expected_entity` first
   appeared in tool output.
5. **Attribute** the row to one of four buckets
   (`graph_rag_graph_agent/eval/oracle.py::attribute_status`):

   | Status | Definition |
   |---|---|
   | `agent_ok` | Oracle returned ≥1 rows AND the agent answered correctly. |
   | `agent_miss` | Oracle returned ≥1 rows AND the agent answered wrong / partial — a reasoning failure, recoverable. |
   | `extraction_miss` | Graph agent only: oracle returned 0 rows or the question has no oracle. The graph itself doesn't support the answer; not tunable without re-extracting. |
   | `no_oracle` | Reserved for the rare case of a `seed_cypher` that errors at runtime (a gold-YAML bug), so genuine extraction misses don't get masked. RAG rows always fall back to verdict-only attribution and never carry `extraction_miss`. |

The aggregated `RunSummary` is dumped to
`eval_runs/<run_id>.json` (every turn, every field above) and a quick
per-category Rich table is printed to the terminal.

### What `eval_report.md` contains

`graph_rag_graph_agent/eval/report.py` renders the latest (or a
specified) run as markdown with these sections:

1. **Accuracy by category** — mean judge score per category per
   agent, plus an overall row.
2. **Latency** — mean and p95 wall-clock seconds per agent.
3. **Tool-call counts** — mean tool calls per question per category
   per agent (a proxy for retrieval / refinement effort).
4. **Failure attribution** — per category and agent, the count of
   each `agent_ok` / `agent_miss` / `extraction_miss` / `no_oracle`
   bucket. This is the section that turns a single mean like
   `negation 0.25 (n=4)` into "X were `agent_miss`, Y were
   `extraction_miss`".
5. **`find_rel_types_like` coverage (graph agent)** — for every
   gold question with `concepts_in_question`, did the graph agent
   probe each concept via `find_rel_types_like`? Useful for
   testing whether prompt-level recipes are actually being
   followed.
6. **Per-question detail** — question, expected answer, oracle
   row count, then for each agent: verdict, latency, tool-call
   count, step-cap signal, oracle status, judge rationale, and a
   400-char preview of the answer.

The report is written to repo-root `eval_report.md` (gitignored).
The citable copy lives under `iterations/<id>/eval_report.md` once
you cut an iteration.

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
    rag_agent.py         chunk-RAG ReAct agent (24-step recursion cap).
                         Exposes `ask(...)` for chat and `ask_with_trace(...)`
                         returning (answer, raw langgraph messages) for eval.
    graph_agent.py       text-to-Cypher ReAct agent (40-step recursion cap).
                         Same (ask, ask_with_trace) contract.
    memory.py            scratchpad_read / scratchpad_write / scratchpad_clear
    common.py            BASE_PERSONA, prompt helpers, and the AgentRun
                         dataclass shared by both agents' ask_with_trace
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
    judge.py             LLM-as-judge (default gpt-4o)
    oracle.py            run each gold question's seed_cypher and
                         attribute rows to agent_ok / agent_miss /
                         extraction_miss / no_oracle
    trace.py             extract tool-call trace, Cypher telemetry,
                         recursion-limit signal, and find_rel_types_like
                         coverage from the LangGraph message list
    run.py               per-question loop: agent -> judge -> oracle
                         -> trace; saves eval_runs/<run_id>.json
    report.py            render eval_report.md from a run JSON
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
