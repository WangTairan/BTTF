# Generated artifacts

This directory contains rebuildable intermediate data and is ignored by Git.

```text
cognascore/embeddings/          SQLite chunk-embedding caches
cognascore/features/base/       Base, visual, chunk, type, and compression tables
cognascore/features/embedding/  Embedding-geometry and clustering tables
cognascore/features/llm/        Causal-LM feature tables
cognascore/llm_surprisal/       Cached token-loss traces
cognascore/calibration/         Label-independent semantic calibration data
source_interference/data/raw/   Upstream source checkouts and acquisition provenance
source_interference/data/base/  Prepared Java and Python source corpora
```

Artifacts are inputs to model-development and frozen-score runners. They are
not evaluation results and should not be cited directly as reported scores.

The source-generation tool uses `artifacts/source_interference/` as its default
workspace. Formal constructed datasets live in `datasets/constructed/`.
