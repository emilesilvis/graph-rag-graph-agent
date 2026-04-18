"""Introspect the Neo4j graph schema for prompt-grounding the text-to-Cypher agent.

The graph.cypher file uses a single node label (`Entity`) with a `name`
property, and a wide variety of relationship types. The agent needs to know
which relationship types actually exist before generating Cypher, otherwise it
will hallucinate.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from graph_rag_graph_agent.config import Config, load_config
from graph_rag_graph_agent.graph.driver import get_driver


@dataclass(frozen=True)
class GraphSchema:
    node_labels: tuple[str, ...]
    node_properties: tuple[str, ...]
    relationship_types: tuple[str, ...]
    sample_entities: tuple[str, ...]

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
        if self.sample_entities:
            lines.append("")
            lines.append(f"  Sample entity names (there are many more):")
            lines.extend(_wrap_list(self.sample_entities, width=100, indent=4))
        return "\n".join(lines)


def _wrap_list(items: tuple[str, ...], width: int, indent: int) -> list[str]:
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

    return GraphSchema(
        node_labels=labels,
        node_properties=props,
        relationship_types=rels,
        sample_entities=samples,
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
