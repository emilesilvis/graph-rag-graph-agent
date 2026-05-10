"""Read-side wrapper around the persisted OWL ontology.

The agent calls three tools that all funnel through this store
(paradigm-symmetric to `pageindex/store.py`):

* `get_ontology_summary()` — a compact view of the TBox: class
  hierarchy after HermiT classification, object-property list with
  domains/ranges, individual counts per class, and any disjointness
  axioms. Body-text-free; analogous to PageIndex's
  `get_document_structure`.
* `run_sparql(query)` — execute a SPARQL query against Owlready2's
  native engine. Returns row-tabulated results with the same
  `(N rows)` footer the graph agent's `run_cypher` uses, so
  `eval/trace.py`'s row-count regex picks it up unchanged.
* `check_consistency(claim)` — temporarily assert one or more triples
  expressed in a tiny `subject property object` mini-format, re-run
  HermiT, return `consistent: True/False` + (if False) the conflicting
  axioms. The paper's signature contribution; cap at 3 calls per
  thread is enforced in the agent's tool wrapper, not here.

The store loads a fresh Owlready2 `World` per process. A second
HermiT run is NOT performed at load time (the build run already
classified the TBox; reading rdfxml back in keeps the inferred
hierarchy because we serialised after `sync_reasoner_hermit`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from graph_rag_graph_agent.config import ONTOLOGY_OWL_PATH


@dataclass
class OntologyStore:
    """In-memory view of the persisted ontology + its raw schema."""

    world: Any
    onto: Any
    schema: dict[str, Any] = field(default_factory=dict)
    base_iri: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "OntologyStore":
        path = path or ONTOLOGY_OWL_PATH
        if not path.exists():
            raise RuntimeError(
                f"Ontology not found at {path}. "
                f"Run: uv run python main.py build-ontology"
            )

        from owlready2 import World

        world = World()
        # `file://` IRI lets Owlready2 read directly from disk without
        # touching the network.
        onto = world.get_ontology(path.as_uri()).load()

        schema_path = path.with_suffix(".schema.json")
        schema: dict[str, Any] = {}
        if schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

        base_iri = str(schema.get("base_iri") or onto.base_iri or "")
        return cls(world=world, onto=onto, schema=schema, base_iri=base_iri)

    def render_summary(self, max_individuals_per_class: int = 12) -> str:
        """Compact TBox + ABox summary (no body text).

        Read once per session by the agent; analogous to
        `PageIndexStore.render_structure`. Designed to fit in a single
        prompt-friendly chunk: classes with their HermiT-classified
        parents, properties with declared domains/ranges, sample
        individuals per class, and the disjointness pairs.
        """
        from owlready2 import Thing

        lines: list[str] = []

        # Classes with their direct parents (post-classification).
        classes = sorted(self.onto.classes(), key=lambda c: c.name)
        if classes:
            lines.append("# Classes (post-HermiT classification)")
            for cls in classes:
                parents = [
                    p.name
                    for p in cls.is_a
                    if hasattr(p, "name") and p is not Thing
                ]
                parent_str = f" : {', '.join(parents)}" if parents else ""
                lines.append(f"- {cls.name}{parent_str}")
            lines.append("")

        # Object properties with declared domain/range.
        obj_props = sorted(self.onto.object_properties(), key=lambda p: p.name)
        if obj_props:
            lines.append("# Object properties")
            for prop in obj_props:
                dom = ", ".join(
                    getattr(d, "name", str(d)) for d in (prop.domain or [])
                )
                rng = ", ".join(
                    getattr(r, "name", str(r)) for r in (prop.range or [])
                )
                line = f"- {prop.name}"
                if dom or rng:
                    line += f"  ({dom or '?'} -> {rng or '?'})"
                lines.append(line)
            lines.append("")

        # Data properties (typically a small number).
        data_props = sorted(self.onto.data_properties(), key=lambda p: p.name)
        if data_props:
            lines.append("# Data properties")
            for prop in data_props:
                rng = ", ".join(
                    getattr(r, "__name__", str(r)) for r in (prop.range or [])
                )
                lines.append(f"- {prop.name}  (-> {rng or '?'})")
            lines.append("")

        # Individuals: count per class + a small sample, so the agent
        # learns the corpus's vocabulary on demand without us dumping
        # every individual at every turn.
        ind_by_class: dict[str, list[str]] = {}
        for ind in self.onto.individuals():
            primary = next(
                (
                    c.name
                    for c in ind.is_a
                    if hasattr(c, "name") and c is not Thing
                ),
                "Thing",
            )
            ind_by_class.setdefault(primary, []).append(ind.name)
        if ind_by_class:
            lines.append("# Individuals (sample per class)")
            for cls_name in sorted(ind_by_class.keys()):
                names = sorted(ind_by_class[cls_name])
                preview = ", ".join(names[:max_individuals_per_class])
                more = (
                    f" (+{len(names) - max_individuals_per_class} more)"
                    if len(names) > max_individuals_per_class
                    else ""
                )
                lines.append(f"- {cls_name} ({len(names)}): {preview}{more}")
            lines.append("")

        disj_pairs = list(self.schema.get("disjointness", []) or [])
        if disj_pairs:
            lines.append("# Disjointness")
            for pair in disj_pairs:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    lines.append(f"- {pair[0]} disjoint {pair[1]}")
            lines.append("")

        inconsistent = list(self.schema.get("inconsistent_classes", []) or [])
        if inconsistent:
            lines.append("# Inconsistent classes (HermiT)")
            for name in inconsistent:
                lines.append(f"- {name}")
            lines.append("")

        lines.append(f"base_iri: {self.base_iri}")
        return "\n".join(lines).strip()

    def run_sparql(self, query: str, max_rows: int = 50) -> str:
        """Execute a SPARQL query against the Owlready2 native engine.

        Returns rows as `col1 | col2 | ...` lines plus a `(N rows)` footer
        matching the graph agent's `run_cypher` shape so the trace
        extractor's row-count regex picks it up. Errors are returned as
        `ERROR: ...` strings (the agent treats this as a hint to revise).
        """
        if not query or not query.strip():
            return "ERROR: empty query."
        try:
            rows = list(self.world.sparql(query))
        except Exception as exc:  # noqa: BLE001 - never raise into the agent
            return f"ERROR: {type(exc).__name__}: {exc}"

        if not rows:
            return "(0 rows)"

        rendered: list[str] = []
        for row in rows[:max_rows]:
            cells = [self._render_cell(c) for c in row]
            rendered.append(" | ".join(cells))
        truncated = ""
        if len(rows) > max_rows:
            truncated = f" (truncated; first {max_rows} of {len(rows)} shown)"
        rendered.append(f"({len(rows)} rows{truncated})")
        return "\n".join(rendered)

    @staticmethod
    def _render_cell(value: Any) -> str:
        if value is None:
            return ""
        name = getattr(value, "name", None)
        if name is not None:
            return str(name)
        return str(value)

    def check_consistency(self, claim: str) -> str:
        """Temporarily assert `claim` triples and re-run HermiT.

        `claim` is a small line-oriented mini-format (one assertion per
        line, three whitespace-separated tokens):

            subject property object             # object property
            subject property "literal value"    # data property

        The triples are added to a *temporary* sub-ontology of the same
        World, HermiT is re-run, and the temporary ontology is then
        destroyed regardless of outcome so the persisted store is not
        mutated. Returns a multi-line block with `consistent: True/False`
        and either the inferred placement or the conflicting axioms.

        This is the symbolic-reasoner-as-validator half of Magaña
        Vsevolodovna & Monti (2025) §3.3, re-shaped as a single tool
        the agent can call to falsify a tentative claim before
        committing to it in its final answer.
        """
        triples = _parse_claim(claim)
        if not triples:
            return (
                "ERROR: could not parse any triple from the claim. "
                "Use one assertion per line, e.g.:\n"
                "  Payments_Service builtWith Python\n"
                "  Auth_Service dependsOn Data_Lineage_Service"
            )

        from owlready2 import Nothing, sync_reasoner_hermit

        # Materialise into a fresh sub-ontology so we can destroy_entity
        # everything we created if HermiT is unhappy.
        sub_iri = f"{self.base_iri or 'http://shopflow.local/onto.owl'}#claim_check"
        scratch = self.world.get_ontology(sub_iri)
        created_inds: list[Any] = []
        applied: list[tuple[Any, Any, Any]] = []
        notes: list[str] = []

        try:
            with scratch:
                for subj_name, prop_name, obj_str in triples:
                    subj = self._lookup_individual(subj_name)
                    if subj is None:
                        notes.append(
                            f"unknown subject '{subj_name}' "
                            f"(skipped this triple)"
                        )
                        continue
                    prop = self._lookup_property(prop_name)
                    if prop is None:
                        notes.append(
                            f"unknown property '{prop_name}' "
                            f"(skipped this triple)"
                        )
                        continue
                    if _is_data_property(prop):
                        value = _coerce_literal(obj_str)
                        current = list(getattr(subj, prop.python_name, []) or [])
                        if value in current:
                            notes.append(
                                f"already asserted: {subj_name} {prop_name} {obj_str}"
                            )
                            continue
                        current.append(value)
                        setattr(subj, prop.python_name, current)
                        applied.append((subj, prop, value))
                    else:
                        obj = self._lookup_individual(obj_str)
                        if obj is None:
                            notes.append(
                                f"unknown object '{obj_str}' "
                                f"(skipped this triple)"
                            )
                            continue
                        current = list(getattr(subj, prop.python_name, []) or [])
                        if obj in current:
                            notes.append(
                                f"already asserted: {subj_name} {prop_name} {obj_str}"
                            )
                            continue
                        current.append(obj)
                        setattr(subj, prop.python_name, current)
                        applied.append((subj, prop, obj))

            consistent = True
            conflicting: list[str] = []
            try:
                with scratch:
                    sync_reasoner_hermit(
                        [self.onto, scratch],
                        infer_property_values=False,
                        debug=0,
                    )
            except Exception as exc:  # noqa: BLE001
                # HermiT raises OwlReadyInconsistentOntologyError on a
                # contradiction. We catch broadly because the Java
                # bridge surfaces several flavours.
                consistent = False
                conflicting.append(f"{type(exc).__name__}: {exc}")

            if consistent:
                # Even if the reasoner did not throw, individual classes
                # may have been classified as Nothing. Surface those.
                for subj, _prop, _obj in applied:
                    for c in getattr(subj, "is_a", []) or []:
                        if c is Nothing:
                            consistent = False
                            conflicting.append(
                                f"{subj.name} was classified as Nothing"
                            )

            if not applied and not notes:
                return "ERROR: no recognisable triples after parsing."

            lines: list[str] = []
            lines.append(f"consistent: {consistent}")
            lines.append(f"asserted_triples: {len(applied)}")
            if notes:
                lines.append("notes:")
                for n in notes:
                    lines.append(f"  - {n}")
            if not consistent and conflicting:
                lines.append("conflicts:")
                for c in conflicting:
                    lines.append(f"  - {c}")
            return "\n".join(lines)

        finally:
            # Roll the scratch ontology back so the next consistency
            # check starts from the same persisted ABox.
            try:
                scratch.destroy()
            except Exception:  # noqa: BLE001
                pass
            for subj, prop, obj in applied:
                try:
                    current = list(getattr(subj, prop.python_name, []) or [])
                    if obj in current:
                        current.remove(obj)
                    setattr(subj, prop.python_name, current)
                except Exception:  # noqa: BLE001
                    pass
            del created_inds  # keep the symbol referenced for clarity

    def _lookup_individual(self, name: str) -> Any | None:
        """Resolve `name` (or its safe-form) to an individual in the loaded ontology."""
        from owlready2 import Thing

        if not name:
            return None
        # Direct hit first (Owlready2 exposes individuals as attributes).
        candidate = getattr(self.onto, name, None)
        if candidate is not None and hasattr(candidate, "is_a"):
            classes = [c for c in candidate.is_a if c is not Thing]
            if classes:
                return candidate
        # Fall back to a scan over individuals — handles spellings the
        # agent uses that diverge slightly from the corpus's canonical
        # form.
        target = name.lower().replace("-", "_").replace(" ", "_")
        for ind in self.onto.individuals():
            if ind.name.lower() == target:
                return ind
        return None

    def _lookup_property(self, name: str) -> Any | None:
        if not name:
            return None
        candidate = getattr(self.onto, name, None)
        if candidate is not None:
            return candidate
        target = name.lower()
        for prop in list(self.onto.object_properties()) + list(
            self.onto.data_properties()
        ):
            if prop.name.lower() == target:
                return prop
        return None


def _parse_claim(claim: str) -> list[tuple[str, str, str]]:
    """Parse the line-oriented claim mini-format.

    Each line: `subject property object` (object may be a quoted literal).
    """
    triples: list[tuple[str, str, str]] = []
    for raw_line in claim.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Try a quoted-literal split first.
        if '"' in line:
            head, _, tail = line.partition('"')
            head = head.strip().split()
            literal = tail.rsplit('"', 1)[0]
            if len(head) == 2 and literal is not None:
                triples.append((head[0], head[1], literal))
                continue
        parts = line.split()
        if len(parts) < 3:
            continue
        subj, prop = parts[0], parts[1]
        obj = " ".join(parts[2:])
        triples.append((subj, prop, obj))
    return triples


def _is_data_property(prop: Any) -> bool:
    from owlready2 import DataProperty

    try:
        return issubclass(prop, DataProperty)
    except TypeError:
        return False


def _coerce_literal(text: str) -> Any:
    s = text.strip()
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1]
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        return int(s)
    except ValueError:
        pass
    return s
