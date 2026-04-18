"""Centralised configuration loaded from environment variables / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _path_env(name: str, default: Path) -> Path:
    """Read a path from env var `name`, falling back to `default`.

    Relative paths are resolved against `PROJECT_ROOT` so invocations from
    other working directories still work.
    """
    raw = os.environ.get(name)
    if not raw:
        return default
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (PROJECT_ROOT / p)


# Swap these via env vars to point the whole pipeline at a different corpus.
KNOWLEDGE_DIR = _path_env("KNOWLEDGE_DIR", PROJECT_ROOT / "knowledge_sources")
GRAPH_CYPHER_PATH = _path_env("GRAPH_CYPHER_PATH", KNOWLEDGE_DIR / "graph.cypher")
CHROMA_DIR = _path_env("CHROMA_DIR", PROJECT_ROOT / ".chroma")

EVAL_DIR = PROJECT_ROOT / "graph_rag_graph_agent" / "eval"
EVAL_QUESTIONS_PATH = EVAL_DIR / "questions.yaml"
EVAL_RUNS_DIR = PROJECT_ROOT / "eval_runs"
EVAL_REPORT_PATH = PROJECT_ROOT / "eval_report.md"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in your .env file (see .env.example)."
        )
    return value


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    agent_model: str
    judge_model: str
    embedding_model: str


@dataclass(frozen=True)
class Config:
    openai: OpenAIConfig
    neo4j: Neo4jConfig
    chroma_collection: str = "knowledge-corpus"


def load_config() -> Config:
    return Config(
        openai=OpenAIConfig(
            api_key=_require("OPENAI_API_KEY"),
            agent_model=os.environ.get("AGENT_MODEL", "gpt-4o-mini"),
            judge_model=os.environ.get("JUDGE_MODEL", "gpt-4o"),
            embedding_model=os.environ.get(
                "EMBEDDING_MODEL", "text-embedding-3-small"
            ),
        ),
        neo4j=Neo4jConfig(
            uri=_require("NEO4J_URI"),
            username=_require("NEO4J_USERNAME"),
            password=_require("NEO4J_PASSWORD"),
        ),
        chroma_collection=os.environ.get("CHROMA_COLLECTION", "knowledge-corpus"),
    )
