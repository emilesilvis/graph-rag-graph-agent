"""Introspect the Neo4j graph schema for prompt-grounding the text-to-Cypher agent.

The graph.cypher file uses a single node label (`Entity`) with a `name`
property, and a wide variety of relationship types. The agent needs to know
which relationship types actually exist before generating Cypher, otherwise it
will hallucinate.

v4 additions:
- `concept_clusters`: groups of rel-type spellings that express the same
  idea (e.g. `IS_BUILT_WITH | IS_DEVELOPED_IN | IS_IMPLEMENTED_IN | BUILT_USING`).
  KGGen emits free-text rel types, so the same English concept ("implemented in")
  often surfaces under multiple morphologically-unrelated spellings. We cluster
  them at schema-load using OpenAI embeddings (paradigm-symmetric to the RAG
  side, which uses embeddings for retrieval). This lets the agent see the
  vocabulary expansion *proactively* in the schema dump rather than relying on
  the discretionary `find_rel_types_like` tool. Clustering uses single-link
  union-find at a conservative threshold (0.62) - clean groupings only,
  singletons drop out.
- `union_for_concept`: query-time embedding-based rel-type lookup. The
  schema caches each rel-type's embedding; the `reach` tool embeds the
  concept phrase at query time and returns every rel type with cosine >=
  0.55 to the concept. This catches cross-cluster synonyms the conservative
  clustering threshold misses (e.g. `DEPENDS_ON` <-> `RELIES_ON` cosine
  0.589, below cluster threshold but above query threshold).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver

# Auxiliary tokens we strip when humanising rel-type names for embedding.
# Linking verbs ("is", "are", "was") and articles carry no concept content;
# stripping them sharpens the embedding. We deliberately KEEP prepositions
# ("on", "in", "with", "by") because they carry semantic load for relations
# - "depends on" embeds notably closer to "relies on" than "depends" does
# to "relies" (cos 0.744 vs 0.454 on text-embedding-3-small).
_EMBED_STOPWORDS = frozenset(
    {
        "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had",
        "the", "a", "an",
        "as", "and", "or",
    }
)

# Larger stopword set used in the token-overlap fallback path: there we
# compare words by 3-char prefix and prepositions cause false positives
# (e.g. "built with" prefix-matching "works with" via the shared "with").
_TOKEN_STOPWORDS = _EMBED_STOPWORDS | frozenset(
    {
        "to", "of", "by", "with", "on", "in", "from", "for", "at",
        "into", "onto", "via",
    }
)

# Cluster threshold tuned empirically on the ShopFlow rel-type set:
# 0.70 with single-link union-find produces crisp groupings
# (BUILT/DEVELOPED/IMPLEMENTED/MAINTAINED/OPERATED all separate cleanly,
# no super-clusters). DEPENDS_ON <-> RELIES_ON has cosine 0.589 - they
# don't cluster, but `union_for_concept` (looser query-time threshold)
# still pairs them when the agent asks.
_CLUSTER_THRESHOLD = 0.70
_MIN_CLUSTER_SIZE = 2

# Concept-lookup threshold for `union_for_concept` and the `reach` tool.
# Deliberately looser than the cluster threshold so cross-cluster
# near-synonyms surface at query time without polluting the prompt-visible
# cluster set. 0.55 catches DEPENDS_ON/RELIES_ON, manage/maintain, and
# build/configure-style spelling drift cleanly.
_CONCEPT_LOOKUP_THRESHOLD = 0.55
# Hard cap on rel-types returned from `union_for_concept`. Prevents a vague
# concept ("use") from producing a Cypher with 50+ rel types in the union,
# which is both slow to execute and a sign the agent is asking the wrong
# question.
_CONCEPT_LOOKUP_MAX_RESULTS = 16


@dataclass(frozen=True)
class ConceptCluster:
    """A group of rel-type spellings that express the same English concept."""

    label: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class GraphSchema:
    node_labels: tuple[str, ...]
    node_properties: tuple[str, ...]
    relationship_types: tuple[str, ...]
    sample_entities: tuple[str, ...]
    concept_clusters: tuple[ConceptCluster, ...] = field(default_factory=tuple)
    # Cached rel-type embeddings (parallel to relationship_types) for
    # query-time concept lookup. Empty tuple if embedding was unavailable
    # at schema fetch.
    rel_type_embeddings: tuple[tuple[float, ...], ...] = field(default_factory=tuple)
    # Humanised phrases parallel to relationship_types, used in rendering
    # and for query-time fallback matching.
    rel_type_phrases: tuple[str, ...] = field(default_factory=tuple)

    def render_for_prompt(self) -> str:
        lines: list[str] = []
        lines.append("Graph schema:")
        lines.append(f"  Node labels: {', '.join(self.node_labels) or '(none)'}")
        lines.append(
            f"  Node properties: {', '.join(self.node_properties) or '(none)'}"
        )
        lines.append(f"  Relationship types ({len(self.relationship_types)} total):")
        wrapped = _wrap_list(self.relationship_types, width=100, indent=4)
        lines.extend(wrapped)

        if self.concept_clusters:
            lines.append("")
            lines.append(
                "  Concept clusters (rel-type spellings that express the "
                "same idea; use the FULL union when a question's verb is "
                "ambiguous about which spelling KGGen used). Singletons "
                "are omitted - call `reach(...)` if your concept doesn't "
                "appear here:"
            )
            for cluster in self.concept_clusters:
                lines.append(f"    - {cluster.label}:")
                lines.extend(_wrap_list(cluster.members, width=100, indent=8))

        if self.sample_entities:
            lines.append("")
            lines.append("  Sample entity names (there are many more):")
            lines.extend(_wrap_list(self.sample_entities, width=100, indent=4))
        return "\n".join(lines)

    def union_for_concept(
        self,
        concept: str,
        threshold: float = _CONCEPT_LOOKUP_THRESHOLD,
        max_results: int = _CONCEPT_LOOKUP_MAX_RESULTS,
    ) -> tuple[str, ...]:
        """Return rel-types semantically closest to the concept phrase.

        Embedding-based cosine search over the cached rel-type embeddings.
        Falls back to substring/prefix-token matching if embeddings aren't
        available (offline / no API key). Result is sorted by descending
        similarity and capped at `max_results`.
        """
        if not concept or not concept.strip():
            return ()
        if self.rel_type_embeddings:
            return self._concept_by_embedding(concept, threshold, max_results)
        return self._concept_by_tokens(concept, max_results)

    def _concept_by_embedding(
        self, concept: str, threshold: float, max_results: int
    ) -> tuple[str, ...]:
        humanised = _humanise_rel_type(concept) or concept.lower().strip()
        embs = _embed_phrases((humanised,))
        if not embs:
            return self._concept_by_tokens(concept, max_results)
        q = embs[0]
        scored: list[tuple[float, str]] = []
        for rt, emb in zip(self.relationship_types, self.rel_type_embeddings):
            sim = _cosine(q, emb)
            if sim >= threshold:
                scored.append((sim, rt))
        scored.sort(key=lambda pair: -pair[0])
        return tuple(rt for _, rt in scored[:max_results])

    def _concept_by_tokens(self, concept: str, max_results: int) -> tuple[str, ...]:
        concept_tokens = _content_tokens(concept)
        if not concept_tokens:
            return ()
        matched: list[str] = []
        for rt in self.relationship_types:
            rt_tokens = _content_tokens(rt.replace("_", " "))
            if _tokens_overlap(concept_tokens, rt_tokens):
                matched.append(rt)
                if len(matched) >= max_results:
                    break
        return tuple(matched)

    def min_pairwise_cosine(self, rel_types: tuple[str, ...]) -> float | None:
        """Min pairwise cosine over the embeddings of the given rel types.

        v5: low values indicate the rel-type set is semantically
        incoherent - e.g. `union_for_concept('developed')` returning
        both `DEVELOPED_BY` (person -> service, ~0.65 cosine to its
        siblings) and `DEVELOPED_IN` (service -> language). When this
        happens a variable-length `reach` traversal will pull in
        neighbours from the wrong rel-class; decomposition into two
        targeted Cypher queries beats it.

        Returns None if <2 rel types or embeddings unavailable.
        """
        if len(rel_types) < 2 or not self.rel_type_embeddings:
            return None
        rt_index = {rt: i for i, rt in enumerate(self.relationship_types)}
        embs: list[tuple[float, ...]] = []
        for rt in rel_types:
            idx = rt_index.get(rt)
            if idx is None or idx >= len(self.rel_type_embeddings):
                continue
            embs.append(self.rel_type_embeddings[idx])
        if len(embs) < 2:
            return None
        min_cos = 1.0
        for i in range(len(embs)):
            for j in range(i + 1, len(embs)):
                c = _cosine(embs[i], embs[j])
                if c < min_cos:
                    min_cos = c
        return min_cos


def _wrap_list(items: Iterable[str], width: int, indent: int) -> list[str]:
    items = tuple(items)
    out: list[str] = []
    pad = " " * indent
    line = pad
    for i, item in enumerate(items):
        sep = "" if line == pad else ", "
        if len(line) + len(sep) + len(item) > width:
            out.append(line)
            line = pad + item
        else:
            line += sep + item
        if i == len(items) - 1:
            out.append(line)
    return out


def _humanise_rel_type(rel: str) -> str:
    """Strip linking verbs and snake_case to make the rel-type embedding-friendly.

    `IS_BUILT_WITH` -> `built with`. `WAS_FORMED_DUE_TO` -> `formed due to`.
    Prepositions are intentionally retained - they're semantically loaded
    for relation-type names. Stripping is conservative: if the result would
    be empty we keep the original tokens so we never embed an empty string.
    """
    parts = [t for t in re.split(r"[_\s]+", rel.lower()) if t]
    stripped = [t for t in parts if t not in _EMBED_STOPWORDS]
    chosen = stripped if stripped else parts
    return " ".join(chosen)


def _content_tokens(text: str) -> tuple[str, ...]:
    """Lowercase content tokens of `text` after stopword/preposition removal.

    Used only by the prefix-token fallback path - prepositions are stripped
    here to avoid false positives via the shared "with"/"on"/"in" tokens.
    """
    out: list[str] = []
    for tok in re.split(r"\W+", text.lower()):
        if len(tok) < 3 or tok in _TOKEN_STOPWORDS:
            continue
        out.append(tok)
    return tuple(out)


def _tokens_overlap(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    """True if any token in `a` shares a >=3-char prefix with any token in `b`."""
    for x in a:
        for y in b:
            if len(x) < 3 or len(y) < 3:
                continue
            if x.startswith(y) or y.startswith(x):
                return True
    return False


def _embed_phrases(phrases: tuple[str, ...]) -> list[list[float]] | None:
    """Embed `phrases` with text-embedding-3-small, returning vectors.

    Returns None on any failure (no API key, network error, etc.); callers
    should fall back to no-embedding behaviour.
    """
    if not phrases:
        return []
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(
            model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
            input=list(phrases),
        )
        return [d.embedding for d in resp.data]
    except Exception:  # noqa: BLE001 - embeddings are best-effort
        return None


def _cosine(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    num = 0.0
    da = 0.0
    db = 0.0
    for x, y in zip(a, b):
        num += x * y
        da += x * x
        db += y * y
    if da == 0 or db == 0:
        return 0.0
    return num / ((da ** 0.5) * (db ** 0.5))


def _cluster_rel_types_by_embedding(
    rels: tuple[str, ...],
    embeddings: list[list[float]],
    threshold: float = _CLUSTER_THRESHOLD,
) -> tuple[ConceptCluster, ...]:
    """Single-link union-find clustering over embedding cosines.

    For each pair (i, j) with cos(emb[i], emb[j]) >= threshold, union the
    two rel types. Single-link is more conservative than greedy-centroid
    on cluster *bloat* (no centroid drift), which on this corpus produces
    cleaner, more interpretable groupings. Singletons are dropped (no
    information value in the prompt).
    """
    if not rels or not embeddings:
        return ()
    n = len(rels)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Precompute norms for efficient cosine
    norms = [sum(v * v for v in emb) ** 0.5 for emb in embeddings]
    for i in range(n):
        if norms[i] == 0:
            continue
        for j in range(i + 1, n):
            if norms[j] == 0:
                continue
            num = sum(a * b for a, b in zip(embeddings[i], embeddings[j]))
            sim = num / (norms[i] * norms[j])
            if sim >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    phrases = [_humanise_rel_type(r) for r in rels]
    out: list[ConceptCluster] = []
    for member_indices in groups.values():
        if len(member_indices) < _MIN_CLUSTER_SIZE:
            continue
        members = tuple(sorted(rels[i] for i in member_indices))
        # Label = shortest member phrase; readable like "built" or
        # "implemented" rather than "actively_involved_in_setting_up".
        label = min((phrases[i] for i in member_indices), key=len)
        out.append(ConceptCluster(label=label, members=members))
    out.sort(key=lambda c: (-len(c.members), c.label))
    return tuple(out)


@lru_cache(maxsize=1)
def _schema_cached(
    uri: str, user: str, password: str, sample_size: int
) -> GraphSchema:
    """Internal cached fetch - cache key includes conn info so tests swap cleanly."""
    driver = get_driver(load_config())
    with driver.session() as session:
        labels_res = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
        labels = tuple(r["label"] for r in labels_res)

        rels_res = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN relationshipType ORDER BY relationshipType"
        )
        rels = tuple(r["relationshipType"] for r in rels_res)

        props_res = session.run(
            "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey ORDER BY propertyKey"
        )
        props = tuple(r["propertyKey"] for r in props_res)

        samples_res = session.run(
            "MATCH (e:Entity) WHERE e.name IS NOT NULL "
            "RETURN e.name AS name ORDER BY e.name LIMIT $n",
            n=sample_size,
        )
        samples = tuple(r["name"] for r in samples_res)

    phrases = tuple(_humanise_rel_type(r) for r in rels)
    embeddings = _embed_phrases(phrases) or []
    if len(embeddings) != len(rels):
        embeddings = []
    clusters = _cluster_rel_types_by_embedding(rels, embeddings) if embeddings else ()

    return GraphSchema(
        node_labels=labels,
        node_properties=props,
        relationship_types=rels,
        sample_entities=samples,
        concept_clusters=clusters,
        rel_type_embeddings=tuple(tuple(e) for e in embeddings),
        rel_type_phrases=phrases,
    )


def fetch_schema(
    config: Config | None = None, sample_size: int = 40
) -> GraphSchema:
    config = config or load_config()
    return _schema_cached(
        config.neo4j.uri,
        config.neo4j.username,
        config.neo4j.password,
        sample_size,
    )


def refresh_schema() -> None:
    _schema_cached.cache_clear()
