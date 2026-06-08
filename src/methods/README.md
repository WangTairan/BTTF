# Methods

Each readability metric lives in its own package:

- `rmc/`: Recursive Masking Complexity, including masking, recovery prompts,
  similarity functions, embeddings, and reports.
- `posnett/`: Posnett readability model; see its `README.md`
  for the published formula and validation scope.
- `scalabrino/`: Scalabrino readability model and released assets.
- `llm_prompt/`: direct LLM readability scoring baseline.
- `cognascore/`: lexeme embedding and DBSCAN cluster-diameter readability method.

New metric implementations should be added as `src/methods/<method>/` packages
with an exported scoring entry point in `__init__.py`. Method-specific runners
and analysis commands belong inside the same method package.
