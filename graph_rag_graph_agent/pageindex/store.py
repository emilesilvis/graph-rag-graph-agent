"""Read-side wrapper around the persisted PageIndex tree.

The agent calls three tools that all funnel through this store:

* `get_document()` -> doc-level metadata (description, root titles, total
  node count) so the agent gets a concise orientation in one call.
* `get_document_structure()` -> the full table of contents (titles +
  summaries + node_ids), with body text stripped so the agent sees the
  navigation aid PageIndex is designed around without paying the token
  cost of every section's text.
* `get_section_content(node_id)` -> the body text of one node (and the
  body of any descendants concatenated, so a single call on a parent
  returns the whole subsection).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from graph_rag_graph_agent.config import PAGEINDEX_TREE_PATH


def _walk(structure: list[dict[str, Any]]):
    for node in structure:
        yield node
        if node.get("nodes"):
            yield from _walk(node["nodes"])


@dataclass
class PageIndexStore:
    """In-memory view of the persisted PageIndex tree."""

    doc_name: str
    doc_description: str
    line_count: int
    structure: list[dict[str, Any]]
    by_id: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: Path | None = None) -> "PageIndexStore":
        path = path or PAGEINDEX_TREE_PATH
        if not path.exists():
            raise RuntimeError(
                f"PageIndex tree not found at {path}. "
                f"Run: uv run python main.py build-pageindex"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        structure = data.get("structure", []) or []
        by_id: dict[str, dict[str, Any]] = {}
        for node in _walk(structure):
            nid = node.get("node_id")
            if isinstance(nid, str):
                by_id[nid] = node
        return cls(
            doc_name=str(data.get("doc_name", "")),
            doc_description=str(data.get("doc_description", "")),
            line_count=int(data.get("line_count", 0) or 0),
            structure=structure,
            by_id=by_id,
        )

    def total_nodes(self) -> int:
        return len(self.by_id)

    def root_titles(self) -> list[str]:
        return [str(n.get("title", "")) for n in self.structure]

    def render_metadata(self) -> str:
        """Concise doc-level summary returned by `get_document`."""
        lines = [
            f"doc_name: {self.doc_name}",
            f"line_count: {self.line_count}",
            f"total_nodes: {self.total_nodes()}",
            f"root_count: {len(self.structure)}",
        ]
        if self.doc_description:
            lines.append(f"description: {self.doc_description}")
        roots = self.root_titles()
        if roots:
            preview = ", ".join(roots[:8])
            more = f" (+{len(roots) - 8} more)" if len(roots) > 8 else ""
            lines.append(f"root_titles: {preview}{more}")
        return "\n".join(lines)

    def render_structure(self, max_summary_chars: int = 240) -> str:
        """Tree-of-contents view: titles + summaries + node_ids, no body.

        Indented by depth so the agent can read it as a navigable outline.
        Summaries are truncated to keep the prompt cost bounded; the agent
        can always call `get_section_content(node_id)` to read the full
        body for any node it wants to inspect.
        """
        lines: list[str] = []

        def render(nodes: list[dict[str, Any]], depth: int) -> None:
            for node in nodes:
                nid = node.get("node_id", "????")
                title = node.get("title", "(untitled)")
                summary = node.get("summary") or node.get("prefix_summary") or ""
                summary = summary.replace("\n", " ").strip()
                if len(summary) > max_summary_chars:
                    summary = summary[: max_summary_chars - 3] + "..."
                indent = "  " * depth
                if summary:
                    lines.append(f"{indent}- [{nid}] {title} - {summary}")
                else:
                    lines.append(f"{indent}- [{nid}] {title}")
                if node.get("nodes"):
                    render(node["nodes"], depth + 1)

        render(self.structure, 0)
        return "\n".join(lines)

    def get_section(self, node_id: str, include_descendants: bool = True) -> str:
        """Return the body text of `node_id`, optionally with its subtree.

        With `include_descendants=True` (default), returns the node's text
        followed by every descendant's text in DFS order. This is usually
        what the agent wants: "give me everything under this heading".
        """
        node = self.by_id.get(node_id)
        if node is None:
            available = sorted(self.by_id.keys())[:20]
            return (
                f"ERROR: node_id '{node_id}' not found. "
                f"First 20 valid ids: {available}"
            )
        if not include_descendants or not node.get("nodes"):
            return str(node.get("text", "") or "").strip()
        parts: list[str] = []
        for n in _walk([node]):
            text = str(n.get("text", "") or "").strip()
            if text:
                parts.append(text)
        return "\n\n".join(parts)
