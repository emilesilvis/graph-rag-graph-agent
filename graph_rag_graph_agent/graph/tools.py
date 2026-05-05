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
                    concept (e.g. "depend" -> DEPENDS_ON, RELIES_ON).
                    Useful for ad-hoc lookups; for actually executing a
                    transitive-reach query, prefer `reach` which does the
                    union for you.
- `reach` (v4, refined v5)   : transitive reach over a concept, with the
                    rel-type union handled automatically. Embeds the concept
                    phrase, finds every rel-type spelling within cosine
                    threshold, builds a variable-length Cypher
                    `[:A|B|C*1..N]` path. v5 additions: silently unions
                    over alias siblings of the source/target (KGGen often
                    emits `Foo Service` and `service-foo-service` as
                    separate nodes - see gold-019); optional `name_filter`
                    to scope categorical questions ("which **services**
                    use Redis"); per-entity zero-match short-circuit that
                    fires after the first dead-end on an entity rather
                    than burning the global 4-call cap; and a
                    coherence-spread warning when the matched rel-type
                    union spans semantically distinct concepts (e.g.
                    "developed" pulling DEVELOPED_BY person AND
                    DEVELOPED_IN language - the gold-016 mixed-concept
                    failure mode).
- `list_entities_like` : case-insensitive substring search over entity names.
- `resolve_entity`      : fuzzy / ranked lookup for ambiguous phrases. v5
                    surfaces alias siblings explicitly so the agent sees
                    that `Auth Service` and `Authentication Service` are
                    likely the same node spelled twice.
- `neighbourhood`       : for a given entity, list outgoing + incoming rel
                    types and sample targets - this is the paradigm-native
                    way to discover how the graph actually connects things
                    before writing Cypher. v5 unions edges over alias
                    siblings.
- `set_difference` (v6) : negation-as-set-subtraction guard rail. Runs a
                    candidate Cypher and an exclude Cypher in one tool
                    call, returns the diff with both source-set sizes and
                    the overlap. v5 traces showed the negation cell was
                    fully reasoning-bound (zero extraction misses) but
                    the agent still wrote single-spelling
                    `NOT EXISTS { -[:REL_TYPE]-> }` filters that miss
                    KGGen's synonymous rel types and silently return the
                    wrong set. Paradigm-symmetric to how `reach` upgraded
                    the v3 transitive recipe from prose to code.

We block any write keywords to prevent the LLM from mutating the graph.
"""

from __future__ import annotations

import difflib
import re
from collections import defaultdict
from typing import Any

from langchain_core.tools import tool

from graph_rag_graph_agent.agents.memory import _current_thread
from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver
from graph_rag_graph_agent.graph.schema import fetch_schema

MAX_ROWS = 50
# Hard cap on `reach` invocations per (thread, agent) session. The prompt
# tells the agent "use reach at most twice" but in practice the LLM
# routinely ignores soft constraints and loops on the most-recently-helpful
# tool when stuck (see v4 attempt 1 - gold-005 hit recursion after 16
# `reach` calls cycling through different concept words on the same
# entity). Code-enforced cap forces a switch in tactic.
_REACH_CALLS_PER_THREAD_LIMIT = 4
_reach_call_counts: dict[str, int] = defaultdict(int)
# v5: per-entity zero-match short-circuit. After the first reach call
# returns 0 matches on a given (thread, entity), subsequent reach calls
# on that entity are refused with a stronger error pointing at
# `neighbourhood` and `list_entities_like`. v4 traces show the agent
# loops on different concept words rather than questioning the entity
# spelling/direction; we want to break that loop before it eats the
# global 4-call budget.
_reach_zero_entities: set[tuple[str, str]] = set()
# v5: alias-sibling cache. Independent of thread because results depend
# only on the entity name and the (read-only) graph state. The eval
# resets this between runs via `reset_alias_cache`.
_alias_cache: dict[str, tuple[str, ...]] = {}
# v5: coherence-spread threshold. If the min pairwise cosine across the
# matched rel-type embeddings drops below this, the union has likely
# collapsed two distinct concepts (e.g. DEVELOPED_BY person <-> 
# DEVELOPED_IN language, cosine ~0.65) and decomposition will beat
# `reach`. Tuned to fire on the gold-016 shape without over-firing
# on cleanly-clustered families like the BUILT/DEVELOPED/IMPLEMENTED
# trio (intra-family pairwise mins ~0.74-0.86).
_REACH_COHERENCE_MIN = 0.70
# v5: width threshold for the broadness warning. >8 spellings under
# one concept usually means the verb is too generic ("use", "have")
# and the agent will get noisy results.
_REACH_BROADNESS_THRESHOLD = 8

# v6: hard cap on `set_difference` invocations per (thread, agent) session.
# Same shape as the reach cap and for the same reason: the agent will
# otherwise iterate on minor query rewrites instead of switching tactics
# when the candidate or exclude set comes back empty/wrong.
_SET_DIFF_CALLS_PER_THREAD_LIMIT = 3
_set_diff_call_counts: dict[str, int] = defaultdict(int)
# v6: marker line emitted by `set_difference` so the trace extractor can
# count adoption (paradigm-symmetric to v5's alias-folded marker and v3's
# find_rel_types_like coverage).
_SET_DIFF_MARKER = "set_difference:"


def reset_reach_state(thread_id: str) -> None:
    """Drop reach + set_difference call-count + zero-match state for a thread."""
    _reach_call_counts.pop(thread_id, None)
    _set_diff_call_counts.pop(thread_id, None)
    for key in [k for k in _reach_zero_entities if k[0] == thread_id]:
        _reach_zero_entities.discard(key)


def reset_alias_cache() -> None:
    """Drop the alias-sibling cache (used between eval runs / when graph reloads)."""
    _alias_cache.clear()

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
# Matches a variable-length pattern with NO rel-type filter: `[*1..4]`,
# `[r*1..N]`, `[*]`. The negative lookahead `[^:\]]*` ensures no `:` appears
# between the opening bracket and the `*`, distinguishing it from
# `[:FOO*1..4]` (which is rel-typed and fine).
_BARE_VARLEN_RE = re.compile(r"\[[^:\]]*\*[^\]]*\]")
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


# v5 alias resolution. KGGen frequently emits the same concept under several
# spellings as separate `:Entity` nodes (e.g. `Auth Service` vs
# `Authentication Service`, `Payments Service` vs `service-payments-service`,
# `Mobile BFF Service` vs `Mobile Backend-for-Frontend (BFF) Service`). We
# don't merge these at load time (the "no graph patching" invariant), so the
# tool layer normalises names to a canonical key and unions over siblings.
_ALIAS_PREFIX_RE = re.compile(r"^(service-|team-|adr-)")
_ALIAS_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*")
# Suffix tokens we strip when computing the alias key. "Service" / "Team"
# carry no discriminating signal between two spellings of the same node
# (e.g. "Auth Service" vs "Authentication Service" - both end in
# "service", and "auth" vs "authentication" share enough fuzzy ratio
# only after the suffix is stripped).
_ALIAS_SUFFIX_TOKENS = frozenset({"service", "team", "app", "system"})
# Synonymous head tokens that should map to the same canonical alias key.
# Catches "Auth"/"Authentication" pair (gold-030); other pairs surface
# automatically via the difflib fallback.
_ALIAS_HEAD_SYNONYMS: dict[str, str] = {
    "authentication": "auth",
    "auth": "auth",
}
_ALIAS_FUZZY_THRESHOLD = 0.85


def _alias_key(name: str) -> str:
    """Normalised key for alias-sibling matching.

    `Payments Service` -> `payments`
    `service-payments-service` -> `payments`
    `Authentication Service` -> `auth`
    `Mobile Backend-for-Frontend (BFF) Service` -> `mobilebackendforfrontend`
    """
    s = name.lower().strip()
    s = _ALIAS_PAREN_RE.sub(" ", s)
    s = _ALIAS_PREFIX_RE.sub("", s)
    tokens = [t for t in re.split(r"[\s_\-]+", s) if t]
    tokens = [t for t in tokens if t not in _ALIAS_SUFFIX_TOKENS]
    if tokens and tokens[0] in _ALIAS_HEAD_SYNONYMS:
        tokens[0] = _ALIAS_HEAD_SYNONYMS[tokens[0]]
    return "".join(tokens)


def _alias_siblings(name: str, driver) -> tuple[str, ...]:
    """Return all entity names that share an alias key with `name`.

    Always includes `name` itself if it exists. Result is cached because
    it depends only on the (read-only) graph state. The eval resets the
    cache between runs via `reset_alias_cache`.
    """
    if name in _alias_cache:
        return _alias_cache[name]
    key = _alias_key(name)
    if not key:
        result = (name,)
        _alias_cache[name] = result
        return result
    siblings: set[str] = {name}
    try:
        with driver.session() as session:
            rows = session.run(
                "MATCH (e:Entity) WHERE e.name IS NOT NULL RETURN e.name AS name"
            )
            all_names = [r["name"] for r in rows]
    except Exception:  # noqa: BLE001 - aliases are best-effort
        result = (name,)
        _alias_cache[name] = result
        return result
    for other in all_names:
        if other == name:
            continue
        if _alias_key(other) == key:
            siblings.add(other)
    # difflib fallback for near-miss spellings the normalisation rules
    # don't catch. Cutoff 0.85 is high enough that genuine pairs match
    # ("Mobile BFF Service" vs "Mobile Backend-for-Frontend (BFF)
    # Service" both normalise to the same key after paren strip; this
    # fallback catches things like singular/plural drift).
    for match in difflib.get_close_matches(
        name, all_names, n=10, cutoff=_ALIAS_FUZZY_THRESHOLD
    ):
        siblings.add(match)
    ordered = tuple(sorted(siblings))
    _alias_cache[name] = ordered
    return ordered


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

    # Bare variable-length paths match every rel-type in the graph and on
    # the KGGen schema (233 types, most of them irrelevant) almost always
    # produce a noisy answer or a runaway query. Surface a NOTE pointing
    # at `reach` / `find_rel_types_like` so the agent constrains the path.
    if _BARE_VARLEN_RE.search(query):
        notes.append(
            "NOTE: variable-length path with no rel-type filter (`[*N..M]`) "
            "matches EVERY edge in the graph. Constrain to a specific "
            "concept: either rewrite as `[:R1|R2|R3*1..N]` after looking "
            "the union up via `find_rel_types_like`, or call the `reach` "
            "tool which does the union for you."
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
    def reach(
        entity_name: str,
        concept: str,
        direction: str = "incoming",
        depth: int = 4,
        limit: int = 25,
        name_filter: str = "",
    ) -> str:
        """Find entities reachable from `entity_name` via a concept (transitive).

        Equivalent to a hand-written Cypher of the form

            MATCH path = (s:Entity)-[:R1|R2|R3*1..depth]->(:Entity {name: ...})

        but builds the rel-type union automatically by embedding-matching
        the concept phrase against the schema. This collapses the two-step
        "find_rel_types_like + run_cypher" recipe into one call - which
        matters because in v3 the agent often invoked find_rel_types_like
        and then ignored its output, querying with different rel types.
        Prefer `reach` over the manual recipe whenever a question is
        transitive ("depends on, directly or indirectly", "downstream",
        "reaches", "is built on top of") AND the relation can plausibly
        be expressed by more than one rel-type spelling.

        v5 behaviour:
        - Silently unions the source/target across alias siblings (e.g.
          a query against `Payments Service` also matches paths anchored
          at `service-payments-service`). The result preamble lists which
          aliases were folded in.
        - `name_filter` (optional substring) restricts results to entities
          whose name contains the filter, case-insensitive. Use this for
          categorical questions: `name_filter='Service'` keeps the answer
          set to services and excludes teams / infra / docs that share
          the same edge-type vocabulary.
        - First time `reach` returns 0 matches on an entity within a
          thread, the next `reach` call on that same entity is refused
          with an error pointing at `neighbourhood` and
          `list_entities_like`. The lesson from v4 traces is that
          re-trying with a different concept word almost never helps;
          the issue is the entity spelling or relation direction.
        - When the matched rel-type union is broad (>8 spellings) or
          semantically incoherent (the verb pulled in two distinct
          relations, e.g. `developed` matching DEVELOPED_BY person and
          DEVELOPED_IN language), a NOTE is appended suggesting either
          a narrower verb, a `name_filter`, or decomposition.

        Args:
            entity_name: the target if direction='incoming', the source if
                direction='outgoing'. Use `resolve_entity` first if unsure
                of the exact spelling - though aliases are now folded in
                automatically.
            concept: an English phrase describing the relation, e.g.
                'depend on', 'manage', 'is implemented in', 'replaced by'.
            direction: 'incoming' (default) finds entities that point AT
                `entity_name` via concept. 'outgoing' finds entities that
                `entity_name` points AT.
            depth: max hops, clamped to 1..8. Default 4.
            limit: max distinct results returned, clamped to 1..50.
                Default 25.
            name_filter: optional case-insensitive substring constraint on
                the names returned (NOT on the source entity). Use for
                "which **services** depend on X" / "which **databases**
                does Y use" style questions.
        """
        thread_id = _current_thread.get()
        _reach_call_counts[thread_id] += 1
        if _reach_call_counts[thread_id] > _REACH_CALLS_PER_THREAD_LIMIT:
            return (
                f"ERROR: `reach` already called {_REACH_CALLS_PER_THREAD_LIMIT} "
                f"times on this question. Stop using `reach`. The issue is not "
                f"the concept word - it is almost certainly the entity name "
                f"(try `list_entities_like` for alternate spellings, e.g. "
                f"`service-payments-service` vs `Payments Service`) or the "
                f"relation direction. Switch tactics: call `neighbourhood` on "
                f"the resolved entity to see what edges actually exist, then "
                f"write Cypher with `run_cypher` directly."
            )
        if (thread_id, entity_name) in _reach_zero_entities:
            return (
                f"ERROR: `reach` already returned 0 matches on entity "
                f"'{entity_name}' on this question. Re-trying with a "
                f"different concept word almost never helps - the issue "
                f"is the ENTITY (alias mismatch: try `list_entities_like` "
                f"to see if KGGen spelled it differently like "
                f"`service-foo-service` vs `Foo Service`) or the relation "
                f"DIRECTION. Call `neighbourhood('{entity_name}')` to see "
                f"what edges actually exist, then write Cypher directly."
            )
        depth = max(1, min(int(depth), 8))
        limit = max(1, min(int(limit), 50))
        direction = direction.lower().strip()
        if direction not in ("incoming", "outgoing"):
            return (
                "ERROR: direction must be 'incoming' or 'outgoing', "
                f"got {direction!r}."
            )
        schema = fetch_schema(config)
        rel_types = schema.union_for_concept(concept)
        if not rel_types:
            return (
                f"No rel types matched concept '{concept}'. Try a simpler "
                f"verb (e.g. 'depend' instead of 'depends on'), or use "
                f"`find_rel_types_like` for a broader fuzzy search."
            )

        union_clause = "|".join(rel_types)
        # name_filter Cypher fragment - empty filter compiles to TRUE so
        # the planner doesn't see a no-op predicate.
        nf = name_filter.strip()
        nf_clause = " AND toLower(name) CONTAINS toLower($nf)" if nf else ""

        if direction == "incoming":
            cy = (
                f"MATCH path = (s:Entity)-[:{union_clause}*1..{depth}]->"
                f"(t:Entity) "
                f"WHERE t.name IN $names AND NOT s.name IN $names "
                f"WITH s.name AS name, min(length(path)) AS hops "
                f"WHERE 1=1{nf_clause} "
                f"ORDER BY hops, name LIMIT $lim "
                f"RETURN name, hops"
            )
        else:
            cy = (
                f"MATCH path = (s:Entity)-[:{union_clause}*1..{depth}]->"
                f"(t:Entity) "
                f"WHERE s.name IN $names AND NOT t.name IN $names "
                f"WITH t.name AS name, min(length(path)) AS hops "
                f"WHERE 1=1{nf_clause} "
                f"ORDER BY hops, name LIMIT $lim "
                f"RETURN name, hops"
            )
        try:
            with driver.session() as session:
                exists = session.run(
                    "MATCH (e:Entity {name: $n}) RETURN e.name AS name LIMIT 1",
                    n=entity_name,
                ).single()
                if exists is None:
                    return (
                        f"No entity named '{entity_name}'. Try `resolve_entity` "
                        f"or `list_entities_like` to find the correct spelling."
                    )
                aliases = _alias_siblings(entity_name, driver)
                rows = session.run(
                    cy, names=list(aliases), lim=limit, nf=nf
                ).data()
        except Exception as exc:  # noqa: BLE001 - surface DB error
            return f"ERROR executing reach: {type(exc).__name__}: {exc}"

        # Coherence + breadth diagnostics on the matched union.
        warnings: list[str] = []
        if len(rel_types) > _REACH_BROADNESS_THRESHOLD:
            warnings.append(
                f"NOTE: concept '{concept}' matched {len(rel_types)} "
                f"rel-type spellings - likely too broad. Try a more "
                f"specific verb, or pass `name_filter` (e.g. 'Service') "
                f"to restrict the answer set by entity-shape."
            )
        spread = schema.min_pairwise_cosine(rel_types)
        if spread is not None and spread < _REACH_COHERENCE_MIN:
            warnings.append(
                f"NOTE: matched rel-type union is semantically "
                f"incoherent (min pairwise cosine {spread:.2f} < "
                f"{_REACH_COHERENCE_MIN:.2f}). The verb '{concept}' "
                f"likely conflates two distinct relations (e.g. "
                f"`DEVELOPED_BY` person vs `DEVELOPED_IN` language). "
                f"For 3-hop chains where each hop is a different "
                f"relation, decompose: resolve the middle entity in one "
                f"`run_cypher` call, stash via `scratchpad_write`, then "
                f"query the next hop separately."
            )

        if not rows:
            _reach_zero_entities.add((thread_id, entity_name))
            alias_note = ""
            if len(aliases) > 1:
                alias_note = f"\n[aliases unioned: {', '.join(aliases)}]"
            warning_block = ("\n" + "\n".join(warnings)) if warnings else ""
            return (
                f"(no matches: no entity reaches '{entity_name}' "
                f"{'<-' if direction == 'incoming' else '->'} via "
                f"`{concept}` within depth {depth})\n"
                f"[rel-types tried: {', '.join(rel_types)}]"
                f"{alias_note}"
                f"{warning_block}"
            )

        lines = [
            f"reach({entity_name!r}, concept={concept!r}, "
            f"direction={direction!r}, depth={depth}"
            + (f", name_filter={nf!r}" if nf else "")
            + f") - union of {len(rel_types)} rel-type spelling"
            f"{'s' if len(rel_types) != 1 else ''}:"
        ]
        lines.append(f"  [{', '.join(rel_types)}]")
        if len(aliases) > 1:
            lines.append(f"  [aliases unioned: {', '.join(aliases)}]")
        lines.append(f"({len(rows)} match{'es' if len(rows) != 1 else ''})")
        for row in rows:
            lines.append(f"  - {row['name']}  (hops={row['hops']})")
        if warnings:
            lines.append("")
            lines.extend(warnings)
        return "\n".join(lines)

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

        v5: when the top match has alias siblings (e.g. KGGen emitted
        both `Auth Service` and `Authentication Service` as separate
        nodes), they are listed under an `aliases:` line so you know
        the entity exists under multiple spellings. `reach` and
        `neighbourhood` silently union over these spellings, so you
        can call them with any of the listed names.
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
        lines = [f"{name}  (score={score:.2f})" for name, score in ranked]
        top_name = ranked[0][0]
        siblings = _alias_siblings(top_name, driver)
        other_aliases = tuple(s for s in siblings if s != top_name)
        if other_aliases:
            lines.append(
                f"aliases of '{top_name}' (same node under different "
                f"spellings; reach/neighbourhood union over these): "
                + ", ".join(other_aliases)
            )
        return "\n".join(lines)

    @tool
    def neighbourhood(entity_name: str, per_rel_limit: int = 3) -> str:
        """Inspect how an entity actually connects to the rest of the graph.

        For the given entity, returns outgoing and incoming relationships
        grouped by type, with a few sample neighbours per type and their
        total count. This is the recommended first step before writing
        Cypher about an entity, because it tells you which relationship
        types actually exist for that specific entity (rather than guessing
        a plausible-sounding one).

        v5: silently unions edges over alias siblings (e.g. queries on
        `Payments Service` also include edges of `service-payments-service`).
        Without this, neighbourhood on the empty-edge spelling returned
        "no relationships" (the gold-019 failure mode).
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
            aliases = _alias_siblings(entity_name, driver)
            out_rows = session.run(
                """
                MATCH (e:Entity)-[r]->(t:Entity)
                WHERE e.name IN $names AND NOT t.name IN $names
                WITH type(r) AS rel, collect(DISTINCT t.name) AS targets
                RETURN rel, size(targets) AS total,
                       targets[0..$k] AS sample
                ORDER BY rel
                """,
                names=list(aliases),
                k=per_rel_limit,
            ).data()
            in_rows = session.run(
                """
                MATCH (e:Entity)<-[r]-(s:Entity)
                WHERE e.name IN $names AND NOT s.name IN $names
                WITH type(r) AS rel, collect(DISTINCT s.name) AS sources
                RETURN rel, size(sources) AS total,
                       sources[0..$k] AS sample
                ORDER BY rel
                """,
                names=list(aliases),
                k=per_rel_limit,
            ).data()
        if not out_rows and not in_rows:
            return f"'{entity_name}' exists but has no relationships."
        header = f"Neighbourhood of '{entity_name}'"
        if len(aliases) > 1:
            header += f" (aliases unioned: {', '.join(aliases)})"
        header += ":"
        lines: list[str] = [header]
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

    @tool
    def set_difference(
        candidate_cypher: str,
        exclude_cypher: str,
        key: str = "name",
        limit: int = 50,
    ) -> str:
        """Compute candidate_set - exclude_set as a guard rail for negation.

        Both Cyphers must RETURN a column named `key` (default 'name').
        The tool runs both queries read-only, computes the set difference
        (candidates whose `key` value is not in the exclude set), and
        returns the result with both source-set sizes shown so the agent
        can sanity-check before answering.

        Use this for "X NOT verb Y" questions instead of writing a single
        `NOT EXISTS { -[:REL_TYPE]-> }` filter. KGGen emits free-text rel
        types and the same English concept ("implemented in") often
        surfaces under five different spellings (IS_BUILT_WITH,
        IS_DEVELOPED_IN, IS_IMPLEMENTED_IN, BUILT_USING, IS_WRITTEN_IN).
        A single-spelling NOT EXISTS silently returns ALL candidates when
        the spelling is wrong - the v5 negation cell (0.25, n=4) is
        100% reasoning-bound failures of exactly this shape.

        Recipe:
            STEP 1: positive set. Write a Cypher returning the candidates,
                aliased `RETURN <expr> AS name` (or your chosen `key`).
                Example: `MATCH (:Entity {name: 'Platform Team'})
                -[:MANAGES]->(s:Entity) RETURN s.name AS name`.
            STEP 2: exclude set. Write a Cypher returning the entities to
                EXCLUDE, same column name. ALWAYS use the FULL rel-type
                union from `find_rel_types_like` / Concept clusters, NOT a
                single spelling. Example for "implemented in Python":
                `MATCH (s:Entity)-[r]->(:Entity {name: 'Python'})
                WHERE type(r) IN ['IS_BUILT_WITH','IS_DEVELOPED_IN',
                'IS_IMPLEMENTED_IN','BUILT_USING','IS_WRITTEN_IN']
                RETURN s.name AS name`.
            STEP 3: pass both to `set_difference`. The result is the
                candidates NOT in the exclude set.

        The output explicitly shows BOTH source-set sizes and the overlap
        count, so a sanity-check of the form "negation answer = candidate
        set minus overlap" is verifiable. If `n_candidates` is 0 the
        candidate Cypher is wrong; if `n_excluded` is 0 the exclude
        Cypher missed the rel-type union and the diff degenerates to the
        entire candidate set (the gold-028 / gold-029 / gold-030 failure
        mode in v4/v5).

        Args:
            candidate_cypher: Cypher for the positive set, must RETURN a
                column named `key`.
            exclude_cypher: Cypher for the exclude set, must RETURN a
                column named `key`.
            key: column name to extract from both result sets. Default
                'name'. Both Cyphers must use the same column name.
            limit: max distinct results returned, clamped to 1..200.
        """
        thread_id = _current_thread.get()
        _set_diff_call_counts[thread_id] += 1
        if _set_diff_call_counts[thread_id] > _SET_DIFF_CALLS_PER_THREAD_LIMIT:
            return (
                f"ERROR: `set_difference` already called "
                f"{_SET_DIFF_CALLS_PER_THREAD_LIMIT} times on this question. "
                f"Stop iterating on the queries - the issue is almost "
                f"certainly the rel-type union in your EXCLUDE Cypher (use "
                f"`find_rel_types_like` for the FULL set of spellings) or "
                f"a wrong CANDIDATE pattern. Inspect the prior result's "
                f"`candidates` and `excluded` lines and adjust deliberately."
            )
        if not _is_read_only(candidate_cypher) or not _is_read_only(exclude_cypher):
            return (
                "ERROR: set_difference rejected - both queries must be "
                "read-only. Remove CREATE / MERGE / DELETE / SET / REMOVE."
            )
        limit = max(1, min(int(limit), 200))
        key = (key or "name").strip() or "name"

        notes: list[str] = []
        notes.extend(_preflight_cypher(candidate_cypher, config))
        notes.extend(_preflight_cypher(exclude_cypher, config))

        def _run(cypher: str, label: str) -> tuple[list[str] | None, str | None]:
            try:
                with driver.session() as session:
                    result = session.run(cypher)
                    rows = list(result)
            except Exception as exc:  # noqa: BLE001
                return None, f"ERROR running {label} Cypher: {type(exc).__name__}: {exc}"
            values: list[str] = []
            seen: set[str] = set()
            for row in rows:
                if key not in row.keys():
                    available = ", ".join(row.keys())
                    return None, (
                        f"ERROR: {label} Cypher must RETURN a column named "
                        f"'{key}'. Available columns: {available}. Rewrite "
                        f"the RETURN clause as `RETURN <expr> AS {key}`."
                    )
                v = row[key]
                if v is None:
                    continue
                s = str(v)
                if s in seen:
                    continue
                seen.add(s)
                values.append(s)
            return values, None

        candidates, err = _run(candidate_cypher, "candidate")
        if err:
            return err
        excluded, err = _run(exclude_cypher, "exclude")
        if err:
            return err

        candidates = candidates or []
        excluded = excluded or []
        excluded_set = set(excluded)
        overlap = [c for c in candidates if c in excluded_set]
        result = [c for c in candidates if c not in excluded_set][:limit]

        def _fmt(items: list[str], cap: int = 12) -> str:
            if not items:
                return "(empty)"
            shown = items[:cap]
            tail = f", +{len(items) - cap} more" if len(items) > cap else ""
            return ", ".join(shown) + tail

        lines: list[str] = []
        lines.append(
            f"{_SET_DIFF_MARKER} {len(candidates)} candidates - "
            f"{len(overlap)} excluded (overlap) = {len(result)} in result."
        )
        lines.append(f"  candidates ({len(candidates)}): {_fmt(candidates)}")
        lines.append(f"  excluded   ({len(excluded)}): {_fmt(excluded)}")
        lines.append(f"  overlap    ({len(overlap)}): {_fmt(overlap)}")
        lines.append("")
        if not result:
            if not candidates:
                lines.append(
                    "(empty result, but candidates is also empty - the "
                    "CANDIDATE Cypher matched nothing; fix that first)"
                )
            elif not excluded:
                lines.append(
                    "(empty result is suspicious: exclude set is empty, "
                    "so the diff should equal the candidate set. Check "
                    "the EXCLUDE Cypher's rel-type union with "
                    "`find_rel_types_like`.)"
                )
            else:
                lines.append(
                    "(empty result: every candidate is also in the exclude "
                    "set - the answer to this NOT-question really is "
                    "'none', or the candidate Cypher is too narrow.)"
                )
        else:
            lines.append(f"result ({len(result)}):")
            for name in result:
                lines.append(f"  - {name}")
        if notes:
            lines.append("")
            lines.extend(notes)
        return "\n".join(lines)

    return [
        run_cypher,
        list_relationship_types,
        find_rel_types_like,
        reach,
        list_entities_like,
        resolve_entity,
        neighbourhood,
        set_difference,
    ]
