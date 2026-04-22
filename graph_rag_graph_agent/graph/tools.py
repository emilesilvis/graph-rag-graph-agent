"""Graph tools exposed to the text-to-Cypher agent.

Tools are intentionally small and composable:

- `run_cypher`   : execute a read-only Cypher query; result rows are formatted
                    as compact text, capped at a row limit so the agent never
                    floods its own context. Queries are pre-flighted against
                    the live schema: rel types / property keys that don't
                    exist surface as helpful NOTEs alongside the result so
                    the agent can self-correct rather than looping on
                    hallucinated vocabulary.
- `list_relationship_types` : list every edge type that actually exists.
- `find_rel_types_like` : rank rel types by semantic match to an English
                    concept (e.g. "depend" -> DEPENDS_ON, RELIES_ON,
                    IS_DEPENDENCY_OF). Essential before variable-length
                    paths, `-[:A|B]->` unions, or `NOT EXISTS` filters on
                    a KGGen graph where one concept often has several
                    spellings.
- `list_entities_like` : case-insensitive substring search over entity names.
- `resolve_entity`      : fuzzy / ranked lookup for ambiguous phrases.
- `neighbourhood`       : for a given entity, list outgoing + incoming rel
                    types and sample targets - this is the paradigm-native
                    way to discover how the graph actually connects things
                    before writing Cypher.

We block any write keywords to prevent the LLM from mutating the graph.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

from langchain_core.tools import tool

from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver
from graph_rag_graph_agent.graph.schema import fetch_schema

MAX_ROWS = 50

_FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|CALL\s+apoc\.\w+\.(create|delete|update)|"
    r"FOREACH)\b",
    re.IGNORECASE,
)

# Matches `[:FOO]`, `[:FOO|BAR]`, `[:FOO*1..4]`, `[r:FOO|BAR]` etc.
# Captures the pipe-separated list of rel types.
_REL_TYPE_RE = re.compile(
    r"\[\s*(?:[A-Za-z_][\w]*)?\s*:\s*([A-Z_][A-Z0-9_|\s]*?)\s*(?:\*[0-9.\s]*)?\]"
)
# Matches `<var>.<prop>` references such as `author.role`. Filters out
# numeric access (`r[0]`) and method calls (`.items()`).
_PROP_REF_RE = re.compile(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b")
_CYPHER_KEYWORDS = {
    "AND", "OR", "NOT", "WHERE", "RETURN", "MATCH", "WITH", "LIMIT",
    "ORDER", "BY", "AS", "IN", "IS", "NULL", "TRUE", "FALSE", "COUNT",
    "COLLECT", "DISTINCT", "OPTIONAL", "UNWIND", "CALL", "YIELD",
}


def _is_read_only(cypher: str) -> bool:
    return _FORBIDDEN.search(cypher) is None


def _suggest(name: str, universe: tuple[str, ...], n: int = 3) -> list[str]:
    return difflib.get_close_matches(name, universe, n=n, cutoff=0.5)


def _preflight_cypher(query: str, config: Config) -> list[str]:
    """Return a list of schema-validation NOTE lines for `query`.

    We only emit notes for tokens the agent clearly *intended* as rel types
    or property keys (via Cypher syntax). This catches the common failure
    mode where the LLM invents a plausible-sounding edge type (e.g.
    `:IS_IMPLEMENTED_AS`) that the graph does not actually have. Empty
    result sets then get annotated with "that rel type does not exist -
    did you mean X, Y, Z?" so the agent can retry.
    """
    try:
        schema = fetch_schema(config)
    except Exception:  # noqa: BLE001
        return []
    known_rels = set(schema.relationship_types)
    known_props = set(schema.node_properties)
    notes: list[str] = []

    seen_rels: set[str] = set()
    for match in _REL_TYPE_RE.finditer(query):
        raw = match.group(1)
        for rt in re.split(r"\s*\|\s*", raw):
            rt = rt.strip()
            if not rt or rt in seen_rels:
                continue
            seen_rels.add(rt)
            if rt not in known_rels:
                near = _suggest(rt, tuple(known_rels))
                hint = f" Did you mean: {', '.join(near)}?" if near else ""
                notes.append(
                    f"NOTE: relationship type `{rt}` does not exist in this graph.{hint}"
                )

    seen_props: set[str] = set()
    for match in _PROP_REF_RE.finditer(query):
        prop = match.group(2)
        if prop in _CYPHER_KEYWORDS or prop in seen_props:
            continue
        seen_props.add(prop)
        if prop not in known_props:
            near = _suggest(prop, tuple(known_props))
            hint = f" Did you mean: {', '.join(near)}?" if near else ""
            notes.append(
                f"NOTE: property key `{prop}` is not in the schema. "
                f"In this graph, attributes may be modelled as neighbour "
                f"entities (e.g. `(x)-[:HAS_ROLE]->(role:Entity)`) rather "
                f"than properties.{hint}"
            )

    return notes


def _format_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_format_value(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_format_value(v)}" for k, v in value.items()) + "}"
    if hasattr(value, "items") and hasattr(value, "labels"):
        return f"({','.join(value.labels)} {dict(value.items())})"
    return str(value)


def _format_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(0 rows)"
    keys = list(rows[0].keys())
    lines = [" | ".join(keys)]
    lines.append("-" * len(lines[0]))
    for row in rows:
        lines.append(" | ".join(_format_value(row.get(k)) for k in keys))
    lines.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)


def build_graph_tools(config: Config | None = None) -> list[Any]:
    config = config or load_config()
    driver = get_driver(config)

    @tool
    def run_cypher(query: str) -> str:
        """Execute a read-only Cypher query against the knowledge graph.

        The graph has a single node label `Entity` with a `name` property, and
        many relationship types (see the system prompt for the full list).

        Rules:
        - Read-only: CREATE / MERGE / DELETE / SET / REMOVE etc. are rejected.
        - Results are truncated to 50 rows - add your own LIMIT if you expect
          more and want deterministic ordering.
        - Entity names are case-sensitive; use `list_entities_like` first if
          you're not sure of the exact spelling.

        Returns a text table of the result rows.
        """
        if not _is_read_only(query):
            return (
                "ERROR: Cypher rejected - this tool only allows read-only queries. "
                "Remove CREATE / MERGE / DELETE / SET / REMOVE / DROP."
            )
        preflight_notes = _preflight_cypher(query, config)
        try:
            with driver.session() as session:
                result = session.run(query)
                rows = []
                for record in result:
                    rows.append(dict(record))
                    if len(rows) >= MAX_ROWS:
                        break
        except Exception as exc:  # noqa: BLE001 - surface DB error to the agent
            return f"ERROR executing Cypher: {type(exc).__name__}: {exc}"
        truncated = len(rows) >= MAX_ROWS
        out = _format_rows(rows)
        if truncated:
            out += f"\n[NOTE] Output truncated at {MAX_ROWS} rows."
        if preflight_notes:
            out += "\n" + "\n".join(preflight_notes)
        return out

    @tool
    def list_relationship_types() -> str:
        """List every relationship type present in the graph."""
        schema = fetch_schema(config)
        return ", ".join(schema.relationship_types)

    @tool
    def find_rel_types_like(concept: str, limit: int = 10) -> str:
        """Find relationship types in the schema that match a concept.

        KGGen emits free-text rel types, so a single English verb often maps
        to several edge spellings (e.g. "depend" -> DEPENDS_ON, RELIES_ON,
        IS_DEPENDENCY_OF). Use this BEFORE writing a variable-length path,
        a `NOT EXISTS {...}` filter, or a `-[:X|Y|Z]->` union so the query
        doesn't silently miss edges that express the same relation under a
        different spelling.

        Matches by case-insensitive substring first, then by difflib fuzzy
        similarity for anything missed. Returns a ranked list, highest
        confidence first. If nothing matches, falls back to the closest
        fuzzy matches so the agent gets a hint rather than an empty list.
        """
        limit = max(1, min(int(limit), 50))
        schema = fetch_schema(config)
        rel_types = list(schema.relationship_types)
        if not rel_types:
            return "(no relationship types in the current schema)"
        needle = concept.strip().lower()
        if not needle:
            return "(empty concept; pass a word like 'depend' or 'manage')"
        tokens = [t for t in re.split(r"\W+", needle) if t]
        scored: dict[str, float] = {}
        for rt in rel_types:
            rt_lower = rt.lower()
            substring_hit = False
            for tok in tokens or [needle]:
                if tok and tok in rt_lower:
                    substring_hit = True
                    break
            ratio = difflib.SequenceMatcher(None, needle, rt_lower).ratio()
            score = ratio + (0.5 if substring_hit else 0.0)
            if substring_hit or ratio >= 0.5:
                scored[rt] = max(scored.get(rt, 0.0), score)
        if not scored:
            for match in difflib.get_close_matches(needle, [r.lower() for r in rel_types], n=limit, cutoff=0.3):
                for rt in rel_types:
                    if rt.lower() == match:
                        scored[rt] = difflib.SequenceMatcher(None, needle, match).ratio()
        if not scored:
            return f"No relationship types resemble '{concept}'."
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return "\n".join(f"{rt}  (score={score:.2f})" for rt, score in ranked)

    @tool
    def list_entities_like(pattern: str, limit: int = 20) -> str:
        """Find entity names containing `pattern` (case-insensitive).

        Use this to disambiguate phrasings before writing Cypher (e.g. to
        discover whether the graph stores a short form or a long form of
        a name).
        """
        limit = max(1, min(int(limit), 50))
        with driver.session() as session:
            result = session.run(
                "MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($p) "
                "RETURN e.name AS name ORDER BY e.name LIMIT $n",
                p=pattern,
                n=limit,
            )
            names = [r["name"] for r in result]
        if not names:
            return f"No entities match '{pattern}'."
        return "\n".join(names)

    @tool
    def resolve_entity(phrase: str, limit: int = 5) -> str:
        """Resolve an ambiguous phrase to the closest entity names in the graph.

        Use this when the question refers to an entity by description
        ("the ADR about the X acquisition", "the team that handles Y")
        rather than its exact canonical name. Returns a ranked list of
        candidates by substring match and fuzzy string similarity.
        """
        limit = max(1, min(int(limit), 20))
        tokens = [t for t in re.split(r"\W+", phrase) if len(t) >= 3]
        if not tokens:
            tokens = [phrase]
        scored: dict[str, float] = {}
        with driver.session() as session:
            for tok in tokens:
                result = session.run(
                    "MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($p) "
                    "RETURN e.name AS name LIMIT 200",
                    p=tok,
                )
                for r in result:
                    name = r["name"]
                    ratio = difflib.SequenceMatcher(
                        None, phrase.lower(), name.lower()
                    ).ratio()
                    scored[name] = max(scored.get(name, 0.0), ratio + 0.25)
            if not scored:
                result = session.run(
                    "MATCH (e:Entity) WHERE e.name IS NOT NULL RETURN e.name AS name"
                )
                all_names = [r["name"] for r in result]
                for n in difflib.get_close_matches(phrase, all_names, n=20, cutoff=0.4):
                    scored[n] = difflib.SequenceMatcher(
                        None, phrase.lower(), n.lower()
                    ).ratio()
        if not scored:
            return f"No entities found resembling '{phrase}'."
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return "\n".join(f"{name}  (score={score:.2f})" for name, score in ranked)

    @tool
    def neighbourhood(entity_name: str, per_rel_limit: int = 3) -> str:
        """Inspect how an entity actually connects to the rest of the graph.

        For the given entity, returns outgoing and incoming relationships
        grouped by type, with a few sample neighbours per type and their
        total count. This is the recommended first step before writing
        Cypher about an entity, because it tells you which relationship
        types actually exist for that specific entity (rather than guessing
        a plausible-sounding one).
        """
        per_rel_limit = max(1, min(int(per_rel_limit), 10))
        with driver.session() as session:
            exists = session.run(
                "MATCH (e:Entity {name: $n}) RETURN e.name AS name LIMIT 1",
                n=entity_name,
            ).single()
            if exists is None:
                return (
                    f"No entity named '{entity_name}'. Try `resolve_entity` or "
                    f"`list_entities_like` to find the correct spelling."
                )
            out_rows = session.run(
                """
                MATCH (e:Entity {name: $n})-[r]->(t:Entity)
                WITH type(r) AS rel, collect(DISTINCT t.name) AS targets
                RETURN rel, size(targets) AS total,
                       targets[0..$k] AS sample
                ORDER BY rel
                """,
                n=entity_name,
                k=per_rel_limit,
            ).data()
            in_rows = session.run(
                """
                MATCH (e:Entity {name: $n})<-[r]-(s:Entity)
                WITH type(r) AS rel, collect(DISTINCT s.name) AS sources
                RETURN rel, size(sources) AS total,
                       sources[0..$k] AS sample
                ORDER BY rel
                """,
                n=entity_name,
                k=per_rel_limit,
            ).data()
        if not out_rows and not in_rows:
            return f"'{entity_name}' exists but has no relationships."
        lines: list[str] = [f"Neighbourhood of '{entity_name}':"]
        if out_rows:
            lines.append("  Outgoing:")
            for r in out_rows:
                sample = ", ".join(r["sample"])
                more = f" (+{r['total'] - len(r['sample'])} more)" if r["total"] > len(r["sample"]) else ""
                lines.append(f"    -[:{r['rel']}]-> {sample}{more}")
        if in_rows:
            lines.append("  Incoming:")
            for r in in_rows:
                sample = ", ".join(r["sample"])
                more = f" (+{r['total'] - len(r['sample'])} more)" if r["total"] > len(r["sample"]) else ""
                lines.append(f"    <-[:{r['rel']}]- {sample}{more}")
        return "\n".join(lines)

    return [
        run_cypher,
        list_relationship_types,
        find_rel_types_like,
        list_entities_like,
        resolve_entity,
        neighbourhood,
    ]
