"""PageIndex variant: vectorless tree-of-contents reasoning RAG.

Generates a hierarchical tree from the corpus's markdown headers,
persists it as JSON, and exposes a `PageIndexStore` for the agent.
The tree-build algorithm is a re-implementation of VectifyAI/PageIndex's
`md_to_tree` markdown mode using the dependencies we already carry
(`langchain_openai` for per-node summary generation), avoiding the
heavyweight upstream deps (`litellm`, `pymupdf`, `PyPDF2`).
"""
