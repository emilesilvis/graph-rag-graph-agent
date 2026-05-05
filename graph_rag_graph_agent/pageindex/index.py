"""Build a PageIndex tree from the markdown corpus.

The corpus's 41 markdown files are concatenated into one buffer with each
filename promoted to a top-level `# <stem>` heading; any pre-existing
`#`/`##`/`###` headings inside the files are demoted by one level so the
filename stem is the canonical top-level node. We then parse markdown
headers, build a tree, and (optionally) attach an LLM-generated summary
per leaf and a prefix-summary per parent. The tree JSON is persisted at
`PAGEINDEX_TREE_PATH` so eval-time runs do not pay the build cost.

Faithful to VectifyAI/PageIndex's markdown-mode algorithm (parse headers,
build tree, summarise) but trimmed to the dependencies we already have.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from rich.console import Console
from tqdm import tqdm

from graph_rag_graph_agent.config import (
    KNOWLEDGE_DIR,
    PAGEINDEX_TREE_PATH,
    Config,
    load_config,
)

console = Console()

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_CODE_FENCE_RE = re.compile(r"^```")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Approximate token count per node. We treat a "token" as ~4 characters,
# which is a rough but stable proxy for OpenAI tokenisation that avoids
# adding `tiktoken` as a hard dependency. Used only to decide whether a
# node's body text is short enough to use verbatim as its summary
# (no LLM call needed) or long enough to warrant a generated summary.
SUMMARY_CHAR_THRESHOLD = 200 * 4  # ~200 tokens
# Cap on summary-generation parallelism. Conservative because we share an
# OpenAI key with the rest of the project.
SUMMARY_WORKERS = 8


@dataclass
class _RawNode:
    title: str
    line_num: int  # 1-indexed
    level: int  # 1..6
    text: str = ""


def _demote_headings(body: str) -> str:
    """Demote every `#...#` header in `body` by one level.

    Skips lines inside fenced code blocks. We cap at 6 (markdown's maximum).
    """
    out: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if _CODE_FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            m = _HEADER_RE.match(line)
            if m:
                hashes, rest = m.group(1), m.group(2)
                new_level = min(len(hashes) + 1, 6)
                out.append("#" * new_level + " " + rest)
                continue
        out.append(line)
    return "\n".join(out)


def _strip_frontmatter(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return text
    return text[m.end() :]


def _concatenate_corpus(knowledge_dir: Path) -> str:
    md_files = sorted(knowledge_dir.glob("*.md"))
    if not md_files:
        raise RuntimeError(f"No markdown files found in {knowledge_dir}")
    parts: list[str] = []
    for path in md_files:
        raw = path.read_text(encoding="utf-8")
        body = _strip_frontmatter(raw)
        demoted = _demote_headings(body)
        parts.append(f"# {path.stem}\n\n{demoted.strip()}\n")
    return "\n\n".join(parts)


def _extract_nodes(markdown: str) -> tuple[list[_RawNode], list[str]]:
    """Walk the markdown line-by-line, collect headers, attach body text.

    Returns (nodes, lines). Each node's `text` is the slice from its own
    header line up to (but not including) the next header line, mirroring
    PageIndex's behaviour.
    """
    lines = markdown.split("\n")
    in_fence = False
    nodes: list[_RawNode] = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if _CODE_FENCE_RE.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADER_RE.match(stripped)
        if not m:
            continue
        hashes, title = m.group(1), m.group(2).strip()
        nodes.append(_RawNode(title=title, line_num=i, level=len(hashes)))

    for idx, node in enumerate(nodes):
        start = node.line_num - 1
        end = nodes[idx + 1].line_num - 1 if idx + 1 < len(nodes) else len(lines)
        node.text = "\n".join(lines[start:end]).strip()

    return nodes, lines


def _build_tree(nodes: list[_RawNode]) -> list[dict[str, Any]]:
    """Build a nested tree of dicts from the flat node list.

    Each node dict gets `title`, `node_id` (sequential, zero-padded 4
    digits, allocated in DFS order at the end), `line_num`, `text`,
    `nodes` (children).
    """
    roots: list[dict[str, Any]] = []
    stack: list[tuple[dict[str, Any], int]] = []
    counter = 1
    for raw in nodes:
        node: dict[str, Any] = {
            "title": raw.title,
            "node_id": str(counter).zfill(4),
            "line_num": raw.line_num,
            "text": raw.text,
            "nodes": [],
        }
        counter += 1
        while stack and stack[-1][1] >= raw.level:
            stack.pop()
        if stack:
            stack[-1][0]["nodes"].append(node)
        else:
            roots.append(node)
        stack.append((node, raw.level))
    return roots


def _walk(structure: list[dict[str, Any]]):
    for node in structure:
        yield node
        if node.get("nodes"):
            yield from _walk(node["nodes"])


_LEAF_PROMPT = (
    "Summarise the following section in 1-2 sentences (<= 40 words). "
    "Focus on what facts the section establishes, not its meta-structure. "
    "Output the summary text only, no preamble.\n\n"
    "---\n{text}\n---"
)
_PARENT_PROMPT = (
    "Below is the body and child-section titles for a parent section. "
    "Summarise in one sentence (<= 30 words) what topics this parent "
    "groups together, so a reader can decide whether to descend. Output "
    "the summary only, no preamble.\n\n"
    "Title: {title}\n"
    "Children: {children}\n"
    "Body excerpt:\n{text}"
)


def _generate_summaries(
    structure: list[dict[str, Any]], llm: ChatOpenAI
) -> None:
    """Attach `summary` (leaves) / `prefix_summary` (parents) in-place.

    Short nodes (body text below `SUMMARY_CHAR_THRESHOLD`) skip the LLM
    and use the raw text - matching PageIndex's behaviour and avoiding
    redundant work on already-tiny sections.
    """
    leaves: list[dict[str, Any]] = []
    parents: list[dict[str, Any]] = []
    for node in _walk(structure):
        if node.get("nodes"):
            parents.append(node)
        else:
            leaves.append(node)

    def summarise_leaf(node: dict[str, Any]) -> tuple[str, str]:
        text = node.get("text", "") or ""
        if len(text) < SUMMARY_CHAR_THRESHOLD:
            return node["node_id"], text
        prompt = _LEAF_PROMPT.format(text=text[:6000])
        resp = llm.invoke([{"role": "user", "content": prompt}])
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        return node["node_id"], content.strip()

    def summarise_parent(node: dict[str, Any]) -> tuple[str, str]:
        text = node.get("text", "") or ""
        children_titles = ", ".join(c["title"] for c in node.get("nodes", []))
        prompt = _PARENT_PROMPT.format(
            title=node["title"],
            children=children_titles or "(none)",
            text=text[:3000],
        )
        resp = llm.invoke([{"role": "user", "content": prompt}])
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        return node["node_id"], content.strip()

    by_id: dict[str, dict[str, Any]] = {n["node_id"]: n for n in _walk(structure)}

    if leaves:
        console.print(f"[dim]Summarising {len(leaves)} leaf nodes...[/dim]")
        with ThreadPoolExecutor(max_workers=SUMMARY_WORKERS) as pool:
            futures = [pool.submit(summarise_leaf, n) for n in leaves]
            for f in tqdm(as_completed(futures), total=len(futures), desc="leaves"):
                node_id, summary = f.result()
                by_id[node_id]["summary"] = summary

    if parents:
        console.print(f"[dim]Summarising {len(parents)} parent nodes...[/dim]")
        with ThreadPoolExecutor(max_workers=SUMMARY_WORKERS) as pool:
            futures = [pool.submit(summarise_parent, n) for n in parents]
            for f in tqdm(as_completed(futures), total=len(futures), desc="parents"):
                node_id, summary = f.result()
                by_id[node_id]["prefix_summary"] = summary


def _generate_doc_description(
    structure: list[dict[str, Any]], llm: ChatOpenAI
) -> str:
    """One-sentence overall description of the corpus from the top-level titles."""
    titles = [n["title"] for n in structure]
    prompt = (
        "Below are the top-level section titles of a knowledge base. "
        "Write a single sentence (<= 30 words) describing what kind of "
        "knowledge base this is. Output the sentence only.\n\n"
        + "\n".join(f"- {t}" for t in titles)
    )
    resp = llm.invoke([{"role": "user", "content": prompt}])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    return content.strip()


def build_tree(
    rebuild: bool = True,
    config: Config | None = None,
    knowledge_dir: Path | None = None,
    out_path: Path | None = None,
    add_summaries: bool = True,
) -> dict[str, Any]:
    """Concatenate the corpus, build a PageIndex tree, persist as JSON.

    Idempotent if `rebuild=False` and the JSON already exists. Returns the
    in-memory tree dict (also written to `out_path`).
    """
    config = config or load_config()
    knowledge_dir = knowledge_dir or KNOWLEDGE_DIR
    out_path = out_path or PAGEINDEX_TREE_PATH

    if not rebuild and out_path.exists():
        console.print(f"[dim]Re-using existing tree at {out_path}[/dim]")
        return json.loads(out_path.read_text(encoding="utf-8"))

    console.print(f"[dim]Concatenating corpus from {knowledge_dir}...[/dim]")
    combined = _concatenate_corpus(knowledge_dir)
    line_count = combined.count("\n") + 1

    raw_nodes, _lines = _extract_nodes(combined)
    structure = _build_tree(raw_nodes)
    console.print(
        f"[green]Parsed {len(raw_nodes)} headings -> "
        f"{len(structure)} root nodes ({line_count} lines).[/green]"
    )

    doc_description = ""
    if add_summaries:
        llm = ChatOpenAI(
            model=config.openai.agent_model,
            api_key=config.openai.api_key,
            temperature=0,
        )
        _generate_summaries(structure, llm)
        doc_description = _generate_doc_description(structure, llm)

    tree = {
        "doc_name": "knowledge_corpus",
        "doc_description": doc_description,
        "line_count": line_count,
        "structure": structure,
        "combined_markdown": combined,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"[green]Tree written to {out_path}[/green]")
    return tree
