# `eval_data/`

Hand-curated gold evaluation sets live here, one per knowledge corpus.

Each YAML is a list of `QAPair` objects (see
`graph_rag_graph_agent/eval/generate.py`). The format is the same as the
auto-generated `graph_rag_graph_agent/eval/questions.yaml`, so either can
be passed to `main.py eval -q <path>`.

Guidelines for a *fair* gold set (important for the experiment to mean
anything — see README.md "Experimental integrity"):

1. Write questions from a user-persona brief, not by inspecting the graph
   or the wiki. Ideally have someone else write them.
2. After writing, verify each answer is reproducible from both the raw
   corpus text AND the graph. Discard any that aren't.
3. Don't iterate on agent prompts based on which questions they get
   wrong — that's classic test-set overfitting.
