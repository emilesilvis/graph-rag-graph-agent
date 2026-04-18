"""Generate an evaluation question set by sampling graph structures.

For each category we:
  1. Sample a handful of concrete structural instances from Neo4j (paths,
     shared neighbors, aggregations, ...).
  2. Ask an LLM to turn each instance into a natural-language question +
     expected answer entities, targeting the weakness of chunk-RAG that the
     category is designed to probe.
  3. Write the result to `eval/questions.yaml` for human review.

Categories:
  - one_hop           : single edge  (a)-[r]->(b)
  - multi_hop_2       : two edges    (a)-[r1]->(b)-[r2]->(c)
  - multi_hop_3       : three edges  (a)-[r1]->(b)-[r2]->(c)-[r3]->(d)
  - dependency_chain  : transitive DEPENDS_ON chain
  - shared_neighbor   : two entities that both point at the same neighbor
  - aggregation_count : how many neighbors an entity has on a given relation
  - negation          : entities that do NOT have a given relation to a target
"""

from __future__ import annotations

import json
import random
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml
from langchain_openai import ChatOpenAI
from rich.console import Console
from tqdm import tqdm

from graph_rag_graph_agent.config import (
    EVAL_QUESTIONS_PATH,
    Config,
    load_config,
)
from graph_rag_graph_agent.graph.driver import get_driver

console = Console()

DEFAULT_PER_CATEGORY = {
    "one_hop": 3,
    "multi_hop_2": 4,
    "multi_hop_3": 3,
    "dependency_chain": 3,
    "shared_neighbor": 3,
    "aggregation_count": 3,
    "negation": 2,
}


@dataclass
class Seed:
    category: str
    description: str
    cypher: str
    answer_entities: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class QAPair:
    id: str
    category: str
    question: str
    expected_answer: str
    expected_entities: list[str]
    seed_cypher: str
    seed_description: str


# --------------------------------------------------------------------------- #
# Clean-entity filter (shape-based, domain-agnostic)
# --------------------------------------------------------------------------- #
#
# Graphs built from documentation often pick up "structural glue" nodes that
# are not human-readable entities (file stems like `team-engineering`, env
# vars like `DB_HOST`, dotfiles like `.env files`). These make bad question
# targets because the corpus prose refers to the real entity by a different
# name. We filter them out using shape heuristics, not a hand-maintained
# allow-list, so the filter transfers to new domains.
#
# If a specific entity still sneaks through, set the optional env var
# `EVAL_ENTITY_BLOCKLIST` to a comma-separated list of exact names.

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){1,}$")  # e.g. service-auth-service
_ENVVAR_RE = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+){1,}$")  # e.g. DB_HOST


def _user_blocklist() -> set[str]:
    raw = __import__("os").environ.get("EVAL_ENTITY_BLOCKLIST", "")
    return {s.strip() for s in raw.split(",") if s.strip()}


def _is_clean_entity(name: str | None) -> bool:
    """True if `name` looks like a human-readable entity.

    Rejects (all shape-based, no per-domain knowledge):
      - slug-shaped identifiers: `team-platform`, `service-auth-service`
      - env-var-shaped identifiers: `DB_HOST`, `NODE_ENV`
      - names starting with `.` (dotfiles): `.env files`
      - anything in the user-supplied EVAL_ENTITY_BLOCKLIST
    """
    if not name or not isinstance(name, str):
        return True  # empty / non-string meta fields are not disqualifying
    if name in _user_blocklist():
        return False
    if name.startswith("."):
        return False
    if _SLUG_RE.match(name):
        return False
    if _ENVVAR_RE.match(name):
        return False
    return True


def _seed_is_clean(seed: "Seed") -> bool:
    # Description sometimes contains the raw entity names; we inspect the
    # structured fields instead.
    candidates: list[str] = []
    candidates.extend(seed.answer_entities)
    for key in ("subject", "target", "a", "b"):
        val = seed.meta.get(key)
        if isinstance(val, str):
            candidates.append(val)
    return all(_is_clean_entity(c) for c in candidates)


# --------------------------------------------------------------------------- #
# Structural samplers
# --------------------------------------------------------------------------- #


def _sample_one_hop(driver, n: int) -> list[Seed]:
    q = """
    MATCH (a:Entity)-[r]->(b:Entity)
    WITH a, type(r) AS rt, b, rand() AS rnd
    ORDER BY rnd LIMIT $n
    RETURN a.name AS a, rt AS rel, b.name AS b
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
    seeds: list[Seed] = []
    for r in rows:
        cy = (
            f"MATCH (:Entity {{name: '{_esc(r['a'])}'}})-[:{r['rel']}]->(b:Entity) "
            f"RETURN b.name AS answer"
        )
        seeds.append(
            Seed(
                category="one_hop",
                description=f"({r['a']})-[:{r['rel']}]->({r['b']})",
                cypher=cy,
                answer_entities=[r["b"]],
                meta={"subject": r["a"], "rel": r["rel"]},
            )
        )
    return seeds


def _sample_multi_hop(driver, n: int, hops: int) -> list[Seed]:
    pattern = "-[r1]->(b:Entity)"
    where_extra = ""
    projection = "a.name AS a, type(r1) AS r1, b.name AS b"
    if hops >= 2:
        pattern += "-[r2]->(c:Entity)"
        where_extra += " AND b <> c AND a <> c"
        projection += ", type(r2) AS r2, c.name AS c"
    if hops >= 3:
        pattern += "-[r3]->(d:Entity)"
        where_extra += " AND c <> d AND a <> d AND b <> d"
        projection += ", type(r3) AS r3, d.name AS d"
    q = f"""
    MATCH (a:Entity){pattern}
    WHERE a <> b{where_extra}
    WITH {projection}, rand() AS rnd
    ORDER BY rnd
    LIMIT $n
    RETURN *
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
    seeds: list[Seed] = []
    for r in rows:
        if hops == 2:
            cy = (
                f"MATCH (:Entity {{name: '{_esc(r['a'])}'}})-[:{r['r1']}]->"
                f"(:Entity {{name: '{_esc(r['b'])}'}})-[:{r['r2']}]->(x:Entity) "
                f"RETURN x.name AS answer"
            )
            desc = (
                f"({r['a']})-[:{r['r1']}]->({r['b']})-[:{r['r2']}]->({r['c']})"
            )
            answers = [r["c"]]
            category = "multi_hop_2"
        else:
            cy = (
                f"MATCH (:Entity {{name: '{_esc(r['a'])}'}})-[:{r['r1']}]->"
                f"(:Entity {{name: '{_esc(r['b'])}'}})-[:{r['r2']}]->"
                f"(:Entity {{name: '{_esc(r['c'])}'}})-[:{r['r3']}]->(x:Entity) "
                f"RETURN x.name AS answer"
            )
            desc = (
                f"({r['a']})-[:{r['r1']}]->({r['b']})-[:{r['r2']}]->"
                f"({r['c']})-[:{r['r3']}]->({r['d']})"
            )
            answers = [r["d"]]
            category = "multi_hop_3"
        seeds.append(
            Seed(category=category, description=desc, cypher=cy, answer_entities=answers)
        )
    return seeds


def _sample_dependency_chain(driver, n: int) -> list[Seed]:
    """Sample transitive chains of any relationship type.

    Category probes multi-hop reachability, not a specific edge name, so
    we use `-[*2..4]->` to stay fully rel-type-agnostic.
    """
    q = """
    MATCH path = (a:Entity)-[*2..4]->(z:Entity)
    WHERE a <> z
    WITH a, z, length(path) AS hops, rand() AS rnd
    ORDER BY rnd LIMIT $n
    RETURN a.name AS a, z.name AS z, hops
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
    seeds: list[Seed] = []
    for r in rows:
        cy = (
            f"MATCH p=(start:Entity)-[*1..6]->"
            f"(:Entity {{name: '{_esc(r['z'])}'}}) "
            f"RETURN DISTINCT start.name AS reaches"
        )
        seeds.append(
            Seed(
                category="dependency_chain",
                description=(
                    f"{r['a']} reaches {r['z']} transitively "
                    f"({r['hops']} hops, any relationship types)"
                ),
                cypher=cy,
                answer_entities=[r["a"]],
                meta={"target": r["z"], "hops": r["hops"]},
            )
        )
    return seeds


def _sample_shared_neighbor(driver, n: int) -> list[Seed]:
    q = """
    MATCH (a:Entity)-[r1]->(t:Entity)<-[r2]-(b:Entity)
    WHERE a <> b AND a.name < b.name
    WITH a, b, t, type(r1) AS r1, type(r2) AS r2, rand() AS rnd
    ORDER BY rnd LIMIT $n
    RETURN a.name AS a, b.name AS b, t.name AS t, r1, r2
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
    seeds: list[Seed] = []
    for r in rows:
        cy = (
            f"MATCH (:Entity {{name: '{_esc(r['a'])}'}})-->(t:Entity)<--"
            f"(:Entity {{name: '{_esc(r['b'])}'}}) RETURN DISTINCT t.name AS shared"
        )
        seeds.append(
            Seed(
                category="shared_neighbor",
                description=(
                    f"Both ({r['a']}) and ({r['b']}) connect to ({r['t']}) "
                    f"via [:{r['r1']}] / [:{r['r2']}]"
                ),
                cypher=cy,
                answer_entities=[r["t"]],
                meta={"a": r["a"], "b": r["b"]},
            )
        )
    return seeds


def _sample_aggregation_count(driver, n: int) -> list[Seed]:
    q = """
    MATCH (a:Entity)-[r]->(b:Entity)
    WITH a, type(r) AS rt, count(DISTINCT b) AS c
    WHERE c >= 3
    WITH a, rt, c, rand() AS rnd
    ORDER BY rnd LIMIT $n
    RETURN a.name AS a, rt AS rel, c AS count
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
    seeds: list[Seed] = []
    for r in rows:
        cy = (
            f"MATCH (:Entity {{name: '{_esc(r['a'])}'}})-[:{r['rel']}]->(b:Entity) "
            f"RETURN count(DISTINCT b) AS count"
        )
        seeds.append(
            Seed(
                category="aggregation_count",
                description=f"({r['a']}) has {r['count']} out-neighbors via [:{r['rel']}]",
                cypher=cy,
                answer_entities=[str(r["count"])],
                meta={"subject": r["a"], "rel": r["rel"], "count": r["count"]},
            )
        )
    return seeds


def _sample_negation(driver, n: int) -> list[Seed]:
    """Ask: among entities that participate in the graph, which do NOT have
    edge R to target T?

    We pick a (target, rel_type) pair where between 2 and 8 entities DO have
    the edge, so the complement is a finite, realistic list. The candidate
    pool is "any entity with at least one outgoing edge" - totally agnostic
    to the domain's specific rel-type vocabulary.
    """
    # First pass: pick plausible (target, rel_type) pairs using whatever rel
    # types exist in the graph.
    q = """
    MATCH (a:Entity)-->()
    WITH DISTINCT a
    WITH collect(a) AS pool, count(*) AS pool_size
    UNWIND pool AS cand
    OPTIONAL MATCH (cand)-[r]->(t:Entity)
    WITH t, type(r) AS rt, count(DISTINCT cand) AS hits, pool_size
    WHERE t IS NOT NULL AND hits >= 2 AND hits <= 8 AND pool_size - hits >= 3
    WITH t, rt, hits, pool_size, rand() AS rnd
    ORDER BY rnd LIMIT $n
    RETURN t.name AS target, rt AS rel, hits, pool_size
    """
    with driver.session() as s:
        rows = list(s.run(q, n=n))
        seeds: list[Seed] = []
        for r in rows:
            # Skip seeds whose target is structural glue; the question would
            # be unanswerable in prose anyway.
            if not _is_clean_entity(r["target"]):
                continue
            # Second pass: compute the actual negatives from the pool.
            neg_rows = s.run(
                f"""
                MATCH (a:Entity)-->()
                WITH DISTINCT a AS cand
                WHERE NOT (cand)-[:{r['rel']}]->(:Entity {{name: $target}})
                RETURN cand.name AS name
                ORDER BY name
                """,
                target=r["target"],
            )
            # Keep only human-readable negatives (top 15).
            negatives = [
                row["name"]
                for row in neg_rows
                if _is_clean_entity(row["name"])
            ][:15]
            if len(negatives) < 3:
                continue
            cy = (
                f"MATCH (s:Entity)-->() "
                f"WITH DISTINCT s "
                f"WHERE NOT (s)-[:{r['rel']}]->(:Entity {{name: '{_esc(r['target'])}'}}) "
                f"RETURN s.name AS negative ORDER BY s.name LIMIT 15"
            )
            seeds.append(
                Seed(
                    category="negation",
                    description=(
                        f"Entities that do NOT have [:{r['rel']}] to ({r['target']})"
                    ),
                    cypher=cy,
                    answer_entities=negatives,
                    meta={
                        "target": r["target"],
                        "rel": r["rel"],
                        "positive_hits": r["hits"],
                        "pool_size": r["pool_size"],
                    },
                )
            )
    return seeds


_SAMPLERS = {
    "one_hop": lambda d, n: _sample_one_hop(d, n),
    "multi_hop_2": lambda d, n: _sample_multi_hop(d, n, 2),
    "multi_hop_3": lambda d, n: _sample_multi_hop(d, n, 3),
    "dependency_chain": lambda d, n: _sample_dependency_chain(d, n),
    "shared_neighbor": lambda d, n: _sample_shared_neighbor(d, n),
    "aggregation_count": lambda d, n: _sample_aggregation_count(d, n),
    "negation": lambda d, n: _sample_negation(d, n),
}


def _esc(name: str) -> str:
    return name.replace("\\", "\\\\").replace("'", "\\'")


# --------------------------------------------------------------------------- #
# LLM question synthesis
# --------------------------------------------------------------------------- #

SYNTH_SYSTEM = """\
You are helping build an evaluation set that compares a chunk-RAG agent
(which retrieves passages from a knowledge corpus by semantic similarity)
against a graph agent (which runs Cypher over a knowledge graph built from
the same corpus).

For each structural seed I give you, write ONE natural-language question a
realistic user might ask, AND the expected answer. The question must:
- Be answerable using only the seed relationship(s) given.
- For `multi_hop_*`, `dependency_chain`, `shared_neighbor`, `aggregation_count`,
  and `negation` categories, phrase the question so that answering it requires
  CONNECTING information that would typically live in different passages.
  This is exactly where chunk retrieval is weak.
- Be written in plain English (no Cypher, no schema jargon).
- For negation questions, phrase as "Which <entities of the relevant kind>
  do NOT ...?" without referring to the graph.

Return ONLY a JSON object with keys:
  question (string), expected_answer (string), expected_entities (list of strings).
`expected_entities` should list the key entity names that a correct answer
must mention.
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _synthesize(llm: ChatOpenAI, seed: Seed, driver) -> QAPair | None:
    # Negation seeds are now produced with `answer_entities` already populated
    # by the sampler (service-shaped candidates only).
    if seed.category == "negation" and not seed.answer_entities:
        return None

    seed_payload = {
        "category": seed.category,
        "structural_description": seed.description,
        "answer_cypher": seed.cypher,
        "known_answer_entities": seed.answer_entities,
        "meta": seed.meta,
    }
    user_msg = (
        "Seed:\n"
        f"{json.dumps(seed_payload, indent=2)}\n\n"
        "Write the question + expected answer as JSON."
    )
    resp = llm.invoke(
        [
            {"role": "system", "content": SYNTH_SYSTEM},
            {"role": "user", "content": user_msg},
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    match = _JSON_RE.search(content)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return QAPair(
        id=f"q-{uuid.uuid4().hex[:8]}",
        category=seed.category,
        question=parsed.get("question", "").strip(),
        expected_answer=parsed.get("expected_answer", "").strip(),
        expected_entities=[
            str(e).strip() for e in parsed.get("expected_entities", seed.answer_entities)
        ],
        seed_cypher=seed.cypher,
        seed_description=seed.description,
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def generate_questions(
    total: int = 25,
    seed: int | None = None,
    out_path: Path | None = None,
    config: Config | None = None,
) -> list[QAPair]:
    """Generate `total` questions distributed over categories and save YAML."""
    config = config or load_config()
    out_path = out_path or EVAL_QUESTIONS_PATH
    if seed is not None:
        random.seed(seed)

    distribution = _scale_distribution(DEFAULT_PER_CATEGORY, total)
    driver = get_driver(config)

    seeds: list[Seed] = []
    for category, count in distribution.items():
        if count <= 0:
            continue
        # Oversample aggressively - after cleaning we may lose many.
        oversample = max(count * 4, count + 4)
        try:
            new_seeds = _SAMPLERS[category](driver, oversample)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Sampler for {category} failed: {exc}[/red]")
            continue
        cleaned = [s for s in new_seeds if _seed_is_clean(s)]
        dropped = len(new_seeds) - len(cleaned)
        if dropped:
            console.print(
                f"[dim]{category}: dropped {dropped}/{len(new_seeds)} noisy seeds[/dim]"
            )
        random.shuffle(cleaned)
        seeds.extend(cleaned[:count])

    console.print(f"[dim]Sampled {len(seeds)} seeds. Synthesising questions...[/dim]")
    llm = ChatOpenAI(
        model=config.openai.agent_model,
        api_key=config.openai.api_key,
        temperature=0.4,
    )

    pairs: list[QAPair] = []
    for seed_obj in tqdm(seeds, desc="synth"):
        pair = _synthesize(llm, seed_obj, driver)
        if pair and pair.question:
            pairs.append(pair)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            [asdict(p) for p in pairs], sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )
    console.print(
        f"[green]Wrote {len(pairs)} questions to {out_path}[/green]"
    )
    return pairs


def _scale_distribution(base: dict[str, int], total: int) -> dict[str, int]:
    base_sum = sum(base.values())
    scale = total / base_sum
    out = {k: max(1, round(v * scale)) for k, v in base.items()}
    # correct rounding drift
    diff = total - sum(out.values())
    if diff != 0:
        keys = list(out.keys())
        i = 0
        step = 1 if diff > 0 else -1
        while diff != 0:
            k = keys[i % len(keys)]
            if step < 0 and out[k] <= 1:
                i += 1
                continue
            out[k] += step
            diff -= step
            i += 1
    return out


def load_questions(path: Path | None = None) -> list[QAPair]:
    path = path or EVAL_QUESTIONS_PATH
    if not path.exists():
        raise RuntimeError(
            f"Question set not found at {path}. "
            f"Run: uv run python main.py generate-eval"
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return [QAPair(**item) for item in raw]
