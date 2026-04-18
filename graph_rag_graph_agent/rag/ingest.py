"""Build a persisted Chroma vector store from the markdown wiki.

Chunking strategy:
  1. Parse YAML frontmatter to extract the page title / page_type / author.
  2. Split by markdown headers so every chunk keeps a section_path like
     "# Auth Service > ## Technical Architecture > ### Dependencies".
  3. Further split oversized sections with a recursive character splitter.

Each chunk keeps metadata so the retriever can cite its source:
    source_file, title, page_type, section_path
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from rich.console import Console
from tqdm import tqdm

from graph_rag_graph_agent.config import (
    CHROMA_DIR,
    KNOWLEDGE_DIR,
    Config,
    load_config,
)

console = Console()

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body_without_frontmatter)."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    body = text[match.end() :]
    return fm, body


def _section_path(header_meta: dict[str, str]) -> str:
    """Turn {'h1': 'Auth Service', 'h2': 'Technical Architecture'} into a path."""
    ordered = [header_meta.get(level) for level in ("h1", "h2", "h3")]
    return " > ".join(h for h in ordered if h)


def _markdown_to_documents(path: Path) -> list[Document]:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(raw)

    title = frontmatter.get("title") or path.stem
    page_type = frontmatter.get("page_type", "unknown")
    author = frontmatter.get("author", "")

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    header_sections = header_splitter.split_text(body)
    if not header_sections:
        header_sections = [Document(page_content=body, metadata={})]

    recursive = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    docs: list[Document] = []
    for section in header_sections:
        section_path = _section_path(section.metadata) or title
        chunks = recursive.split_text(section.page_content)
        for idx, chunk in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source_file": path.name,
                        "title": title,
                        "page_type": page_type,
                        "author": author,
                        "section_path": section_path,
                        "chunk_index": idx,
                    },
                )
            )
    return docs


def _collect_documents(knowledge_dir: Path) -> list[Document]:
    documents: list[Document] = []
    md_files = sorted(knowledge_dir.glob("*.md"))
    if not md_files:
        raise RuntimeError(f"No markdown files found in {knowledge_dir}")

    console.print(f"[dim]Chunking {len(md_files)} markdown files...[/dim]")
    for md_path in tqdm(md_files, desc="chunk"):
        documents.extend(_markdown_to_documents(md_path))
    return documents


def build_index(rebuild: bool = True, config: Config | None = None) -> Chroma:
    """Ingest the wiki into a persisted Chroma collection and return the store."""
    config = config or load_config()

    if rebuild and CHROMA_DIR.exists():
        console.print(f"[yellow]Removing existing index at {CHROMA_DIR}[/yellow]")
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    documents = _collect_documents(KNOWLEDGE_DIR)
    console.print(f"[green]Prepared {len(documents)} chunks.[/green]")

    embeddings = OpenAIEmbeddings(
        model=config.openai.embedding_model,
        api_key=config.openai.api_key,
    )

    console.print("[dim]Embedding and writing to Chroma...[/dim]")
    store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=config.chroma_collection,
        persist_directory=str(CHROMA_DIR),
    )
    console.print(
        f"[green]Chroma index built at {CHROMA_DIR} "
        f"(collection='{config.chroma_collection}')[/green]"
    )
    return store


def open_index(config: Config | None = None) -> Chroma:
    """Open an existing Chroma collection (read path used by the RAG agent)."""
    config = config or load_config()
    if not CHROMA_DIR.exists():
        raise RuntimeError(
            f"Chroma index not found at {CHROMA_DIR}. "
            f"Run: uv run python main.py ingest-rag"
        )
    embeddings = OpenAIEmbeddings(
        model=config.openai.embedding_model,
        api_key=config.openai.api_key,
    )
    return Chroma(
        collection_name=config.chroma_collection,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
