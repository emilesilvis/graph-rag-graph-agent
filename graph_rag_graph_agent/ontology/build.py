"""Build a domain OWL ontology from the markdown corpus.

The 41 markdown files are concatenated into one prompt and a single LLM
call returns a typed JSON schema enumerating classes, object properties,
individuals, assertions, and disjointness pairs. We then materialise the
schema via Owlready2, run HermiT once at build time to classify the
TBox and flag any seeded inconsistencies, and persist as RDF/XML at
`ONTOLOGY_OWL_PATH` together with a JSON sidecar that holds the raw
extraction (so the agent's `get_ontology_summary` tool does not pay the
HermiT-load cost on every question; it loads the persisted ontology
into a fresh Owlready2 World once per process).

Faithful to Magaña Vsevolodovna & Monti (2025) §3.1 for the ontology
construction half (Owlready2 + HermiT, OWL 2 DL with disjointness
axioms). The NL-to-logic semantic parser (their §3.2) is out of scope
for v9 — this paradigm asks the agent to reason in SPARQL + consistency
checks directly rather than via a logistic-regression bridge.

Build cost target: ~30s LLM + a few seconds HermiT. One-time per cut;
the JSON sidecar + RDF/XML are checked into `knowledge_sources/`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from rich.console import Console

from graph_rag_graph_agent.config import (
    KNOWLEDGE_DIR,
    Config,
    load_config,
)

console = Console()

ONTOLOGY_BASE_IRI = "http://shopflow.local/onto.owl"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

_EXTRACTION_PROMPT = """\
You are extracting an OWL 2 DL ontology from a knowledge-base corpus. Read
the corpus below and emit ONE JSON object (no prose, no markdown fence)
with EXACTLY the following keys:

- "classes": list of class names (PascalCase, no spaces). Always include a
  small set of super-classes that organise the domain (e.g. for an
  enterprise wiki: Service, Team, Person, Database, Language, ADR,
  Component, Infrastructure). Add subclasses ONLY when the corpus
  itself draws the distinction (e.g. RelationalDatabase vs CacheDatabase
  if both appear).
- "subclass_of": list of [child, parent] pairs. Both names must appear in
  "classes". Optional; empty list is fine.
- "object_properties": list of objects with keys "name" (camelCase, e.g.
  "managedBy"), "domain" (a class name from "classes" or null), "range"
  (a class name or null). Use null only when the property is genuinely
  cross-cutting; prefer typed.
- "data_properties": list of objects with keys "name" (camelCase) and
  "range" ("string" | "int" | "bool"). Optional; empty list is fine.
- "individuals": list of objects with keys "name" (a stable token, no
  spaces - prefer the corpus's own slug if present) and "class" (a class
  name from "classes"). One individual per real-world entity in the
  corpus. Prefer the corpus's canonical name spelling.
- "assertions": list of objects with keys "subject" (an individual name),
  "property" (an object property name), "object" (an individual name).
  ONE assertion per relationship that is explicit in the corpus. Do
  not infer; do not duplicate.
- "data_assertions": list of objects with keys "subject", "property"
  (a data-property name), "value" (string-encoded literal).
- "disjointness": list of [classA, classB] pairs that should be asserted
  pairwise-disjoint. Use sparingly: only where the corpus would treat
  the two as mutually exclusive (e.g. Service vs Team vs Person are all
  pairwise disjoint; subclass-pairs of the same parent are usually
  disjoint).

Rules:
- Use the corpus's actual spellings for individual names.
- Every assertion's subject and object must appear in "individuals".
- Every assertion's property must appear in "object_properties".
- Output JSON only. No commentary.

Corpus:
---
{corpus}
---
"""

_MAX_CORPUS_CHARS = 120_000


@dataclass
class OntologyBuildResult:
    """In-memory summary of what `build_ontology` produced.

    Mirrors PageIndex's `build_tree` return shape: counts the agent
    sees in `get_ontology_summary` plus the on-disk paths.
    """

    n_classes: int
    n_object_properties: int
    n_data_properties: int
    n_individuals: int
    n_assertions: int
    n_disjointness: int
    inconsistent_classes: list[str]
    owl_path: Path
    schema_path: Path


def _strip_frontmatter(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return text
    return text[m.end():]


def _concatenate_corpus(knowledge_dir: Path) -> str:
    md_files = sorted(knowledge_dir.glob("*.md"))
    if not md_files:
        raise RuntimeError(f"No markdown files found in {knowledge_dir}")
    parts: list[str] = []
    for path in md_files:
        raw = path.read_text(encoding="utf-8")
        body = _strip_frontmatter(raw)
        parts.append(f"# FILE: {path.stem}\n\n{body.strip()}\n")
    combined = "\n\n".join(parts)
    if len(combined) > _MAX_CORPUS_CHARS:
        combined = combined[:_MAX_CORPUS_CHARS]
    return combined


def _strip_json_fence(text: str) -> str:
    """Tolerate models that wrap JSON in a ```json``` fence anyway."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def _extract_schema(corpus: str, llm: ChatOpenAI) -> dict[str, Any]:
    prompt = _EXTRACTION_PROMPT.format(corpus=corpus)
    resp = llm.invoke([{"role": "user", "content": prompt}])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    raw = _strip_json_fence(content)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        snippet = raw[:200].replace("\n", " ")
        raise RuntimeError(
            f"LLM did not return valid JSON for the ontology schema. "
            f"First 200 chars: {snippet!r}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError("Ontology extraction did not return a JSON object.")
    return data


def _safe_name(name: str) -> str:
    """Clamp a name to a valid OWL/Python identifier.

    Owlready2 maps class/property/individual names to Python attributes,
    so we collapse anything non-identifier-safe to underscores. The
    corpus's slug-style spellings (e.g. `service-payments-service`) are
    converted to `service_payments_service` so they round-trip.
    """
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", name.strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned


def _materialise_ontology(schema: dict[str, Any]):
    """Materialise the JSON schema as an Owlready2 ontology and return it."""
    from owlready2 import (
        DataProperty,
        FunctionalProperty,  # noqa: F401  (imported for completeness)
        ObjectProperty,
        Thing,
        World,
        get_ontology,
        types,
    )

    world = World()
    onto = world.get_ontology(ONTOLOGY_BASE_IRI)

    classes = list(schema.get("classes", []) or [])
    subclass_of = list(schema.get("subclass_of", []) or [])
    object_properties = list(schema.get("object_properties", []) or [])
    data_properties = list(schema.get("data_properties", []) or [])
    individuals = list(schema.get("individuals", []) or [])
    assertions = list(schema.get("assertions", []) or [])
    data_assertions = list(schema.get("data_assertions", []) or [])
    disjointness = list(schema.get("disjointness", []) or [])

    cls_lookup: dict[str, Any] = {}
    obj_prop_lookup: dict[str, Any] = {}
    data_prop_lookup: dict[str, Any] = {}
    ind_lookup: dict[str, Any] = {}

    with onto:
        for raw_name in classes:
            name = _safe_name(str(raw_name))
            if name in cls_lookup:
                continue
            cls = types.new_class(name, (Thing,))
            cls_lookup[name] = cls

        # Apply subclass_of by reparenting the existing class objects.
        for pair in subclass_of:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            child_name = _safe_name(str(pair[0]))
            parent_name = _safe_name(str(pair[1]))
            child = cls_lookup.get(child_name)
            parent = cls_lookup.get(parent_name)
            if child is None or parent is None:
                continue
            if parent in child.is_a:
                continue
            child.is_a.append(parent)
            if Thing in child.is_a and any(
                p is not Thing and p in cls_lookup.values() for p in child.is_a
            ):
                # Remove the redundant Thing once we've added a real parent;
                # Owlready2 tolerates Thing in is_a but it clutters the
                # rendered class hierarchy.
                try:
                    child.is_a.remove(Thing)
                except ValueError:
                    pass

        for entry in object_properties:
            if not isinstance(entry, dict):
                continue
            raw_name = entry.get("name")
            if not raw_name:
                continue
            name = _safe_name(str(raw_name))
            if name in obj_prop_lookup:
                continue
            prop = types.new_class(name, (ObjectProperty,))
            domain_raw = entry.get("domain")
            range_raw = entry.get("range")
            domain_cls = cls_lookup.get(_safe_name(str(domain_raw))) if domain_raw else None
            range_cls = cls_lookup.get(_safe_name(str(range_raw))) if range_raw else None
            if domain_cls is not None:
                prop.domain = [domain_cls]
            if range_cls is not None:
                prop.range = [range_cls]
            obj_prop_lookup[name] = prop

        for entry in data_properties:
            if not isinstance(entry, dict):
                continue
            raw_name = entry.get("name")
            if not raw_name:
                continue
            name = _safe_name(str(raw_name))
            if name in data_prop_lookup:
                continue
            prop = types.new_class(name, (DataProperty,))
            range_raw = entry.get("range")
            range_py = {"string": str, "int": int, "bool": bool}.get(
                str(range_raw).lower() if range_raw else "", str
            )
            prop.range = [range_py]
            data_prop_lookup[name] = prop

        for entry in individuals:
            if not isinstance(entry, dict):
                continue
            raw_name = entry.get("name")
            cls_name = entry.get("class")
            if not raw_name or not cls_name:
                continue
            name = _safe_name(str(raw_name))
            if name in ind_lookup:
                continue
            cls = cls_lookup.get(_safe_name(str(cls_name)))
            if cls is None:
                continue
            ind = cls(name)
            ind_lookup[name] = ind

        for entry in assertions:
            if not isinstance(entry, dict):
                continue
            subj = ind_lookup.get(_safe_name(str(entry.get("subject", ""))))
            prop = obj_prop_lookup.get(_safe_name(str(entry.get("property", ""))))
            obj = ind_lookup.get(_safe_name(str(entry.get("object", ""))))
            if subj is None or prop is None or obj is None:
                continue
            current = list(getattr(subj, prop.python_name, []) or [])
            if obj in current:
                continue
            current.append(obj)
            setattr(subj, prop.python_name, current)

        for entry in data_assertions:
            if not isinstance(entry, dict):
                continue
            subj = ind_lookup.get(_safe_name(str(entry.get("subject", ""))))
            prop = data_prop_lookup.get(_safe_name(str(entry.get("property", ""))))
            value = entry.get("value")
            if subj is None or prop is None or value is None:
                continue
            current = list(getattr(subj, prop.python_name, []) or [])
            if value in current:
                continue
            current.append(value)
            setattr(subj, prop.python_name, current)

        # Disjointness axioms. Owlready2 surfaces these via AllDisjoint.
        from owlready2 import AllDisjoint

        for pair in disjointness:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            a = cls_lookup.get(_safe_name(str(pair[0])))
            b = cls_lookup.get(_safe_name(str(pair[1])))
            if a is None or b is None or a is b:
                continue
            AllDisjoint([a, b])

    return world, onto, {
        "classes": cls_lookup,
        "object_properties": obj_prop_lookup,
        "data_properties": data_prop_lookup,
        "individuals": ind_lookup,
    }


def _run_hermit(world, onto) -> list[str]:
    """Run HermiT classification; return the names of any inconsistent classes.

    HermiT can fail (Java not available, ontology too large) — we
    swallow the error and return [] rather than blocking the build, so
    the agent still gets a working store. The eval is a paradigm
    comparison; HermiT fallback is logged not raised.
    """
    from owlready2 import Nothing, sync_reasoner_hermit

    try:
        with onto:
            sync_reasoner_hermit(
                [onto], infer_property_values=False, debug=0
            )
    except Exception as exc:  # noqa: BLE001 - never block build
        console.print(
            f"[yellow]HermiT classification failed ({type(exc).__name__}: "
            f"{exc}). Continuing with the asserted (un-classified) "
            f"ontology.[/yellow]"
        )
        return []

    inconsistent: list[str] = []
    for cls in onto.classes():
        if Nothing in cls.equivalent_to:
            inconsistent.append(cls.name)
    return inconsistent


def build_ontology(
    rebuild: bool = True,
    config: Config | None = None,
    knowledge_dir: Path | None = None,
    out_path: Path | None = None,
) -> OntologyBuildResult:
    """Concatenate the corpus, extract a schema via LLM, run HermiT, persist.

    Idempotent on `rebuild=False` if both the .owl file and the JSON
    sidecar already exist (mirrors `pageindex/index.py:build_tree`).
    """
    from graph_rag_graph_agent.config import ONTOLOGY_OWL_PATH

    config = config or load_config()
    knowledge_dir = knowledge_dir or KNOWLEDGE_DIR
    out_path = out_path or ONTOLOGY_OWL_PATH
    schema_path = out_path.with_suffix(".schema.json")

    if not rebuild and out_path.exists() and schema_path.exists():
        console.print(f"[dim]Re-using existing ontology at {out_path}[/dim]")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        return OntologyBuildResult(
            n_classes=len(schema.get("classes", []) or []),
            n_object_properties=len(schema.get("object_properties", []) or []),
            n_data_properties=len(schema.get("data_properties", []) or []),
            n_individuals=len(schema.get("individuals", []) or []),
            n_assertions=len(schema.get("assertions", []) or []),
            n_disjointness=len(schema.get("disjointness", []) or []),
            inconsistent_classes=list(schema.get("inconsistent_classes", []) or []),
            owl_path=out_path,
            schema_path=schema_path,
        )

    console.print(f"[dim]Concatenating corpus from {knowledge_dir}...[/dim]")
    corpus = _concatenate_corpus(knowledge_dir)

    llm = ChatOpenAI(
        model=config.openai.agent_model,
        api_key=config.openai.api_key,
        temperature=0,
    )

    console.print("[dim]Extracting ontology schema via LLM...[/dim]")
    schema = _extract_schema(corpus, llm)

    console.print("[dim]Materialising ontology via Owlready2...[/dim]")
    world, onto, _lookups = _materialise_ontology(schema)

    console.print("[dim]Running HermiT classification...[/dim]")
    inconsistent = _run_hermit(world, onto)
    if inconsistent:
        console.print(
            f"[yellow]HermiT flagged {len(inconsistent)} inconsistent "
            f"class(es): {inconsistent}[/yellow]"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(out_path), format="rdfxml")
    schema_with_meta = {
        **schema,
        "inconsistent_classes": inconsistent,
        "base_iri": ONTOLOGY_BASE_IRI,
    }
    schema_path.write_text(
        json.dumps(schema_with_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    result = OntologyBuildResult(
        n_classes=len(schema.get("classes", []) or []),
        n_object_properties=len(schema.get("object_properties", []) or []),
        n_data_properties=len(schema.get("data_properties", []) or []),
        n_individuals=len(schema.get("individuals", []) or []),
        n_assertions=len(schema.get("assertions", []) or []),
        n_disjointness=len(schema.get("disjointness", []) or []),
        inconsistent_classes=inconsistent,
        owl_path=out_path,
        schema_path=schema_path,
    )
    console.print(
        f"[green]Ontology written to {out_path}[/green] "
        f"({result.n_classes} classes, "
        f"{result.n_object_properties} object props, "
        f"{result.n_individuals} individuals, "
        f"{result.n_assertions} assertions)"
    )
    return result
