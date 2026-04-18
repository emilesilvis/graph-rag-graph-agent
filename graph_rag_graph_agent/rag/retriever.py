"""Thin wrapper around the Chroma store that formats hits for the LLM."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_chroma import Chroma

from graph_rag_graph_agent.rag.ingest import open_index


@dataclass
class WikiHit:
    title: str
    source_file: str
    section_path: str
    snippet: str
    score: float

    def render(self) -> str:
        return (
            f"[{self.source_file} :: {self.section_path}]\n"
            f"{self.snippet.strip()}"
        )


class WikiRetriever:
    def __init__(self, store: Chroma | None = None) -> None:
        self.store = store or open_index()

    def search(self, query: str, k: int = 5) -> list[WikiHit]:
        raw = self.store.similarity_search_with_relevance_scores(query, k=k)
        hits: list[WikiHit] = []
        for doc, score in raw:
            hits.append(
                WikiHit(
                    title=doc.metadata.get("title", "?"),
                    source_file=doc.metadata.get("source_file", "?"),
                    section_path=doc.metadata.get("section_path", ""),
                    snippet=doc.page_content,
                    score=float(score),
                )
            )
        return hits

    def search_formatted(self, query: str, k: int = 5) -> str:
        hits = self.search(query, k=k)
        if not hits:
            return "No wiki snippets matched that query."
        blocks = [f"--- hit {i + 1} (score={h.score:.3f}) ---\n{h.render()}"
                  for i, h in enumerate(hits)]
        return "\n\n".join(blocks)
