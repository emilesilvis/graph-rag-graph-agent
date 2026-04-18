"""Shared Neo4j driver factory."""

from __future__ import annotations

from functools import lru_cache

from neo4j import Driver, GraphDatabase

from graph_rag_graph_agent.config import Config, load_config


@lru_cache(maxsize=1)
def _cached_driver(uri: str, user: str, password: str) -> Driver:
    return GraphDatabase.driver(uri, auth=(user, password))


def get_driver(config: Config | None = None) -> Driver:
    config = config or load_config()
    return _cached_driver(
        config.neo4j.uri, config.neo4j.username, config.neo4j.password
    )


def close_driver() -> None:
    _cached_driver.cache_clear()
