"""Ontology variant (v9): OWL-ontology + HermiT reasoning over the corpus.

Builds a domain ontology from the markdown corpus by asking the same
`gpt-4o-mini` model that drives the rest of the project to emit a typed
JSON schema (classes, object properties, individuals, assertions,
disjointness), materialises it via Owlready2, runs HermiT once at build
time to classify the TBox + flag inconsistencies, and persists the
result as RDF/XML at `ONTOLOGY_OWL_PATH` so eval-time runs do not pay
the build cost.

Following Magaña Vsevolodovna & Monti (2025; arXiv:2504.07640) for the
ontology-as-symbolic-index half of the pipeline. The NL-to-logic
mapper + iterative-refinement loop from that paper is intentionally
deferred to a hypothetical v10+ — v9 keeps the ontology paradigm a
stand-alone retrieval variant, paradigm-symmetric to v7's PageIndex
addition.
"""
