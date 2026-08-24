# CognaScore

CognaScore is the repository's active code-readability feature pipeline. It
extracts typed cognitive chunks, measures conventional and visual code
properties, embeds selected chunk views, and summarizes embedding geometry and
adaptive cluster structure.

Two reported routes consume the same stable feature tables:

- **CognaScore ML**: a performance-oriented Ridge model using 30 frozen
  features;
- **CognaScore Compact**: an interpretable linear formula restricted to at
  most five features.

Feature selection and ablation code is intentionally outside this package in
`experiments/cognascore/`.

## Package structure

- `extractors/python/`: active `javalang`-based Java extractor with lexical
  support for fragments and other languages;
- `feature_database.py`: base, visual, chunk, type, and compression features;
- `embedding_cache.py`: persistent SQLite embedding cache;
- `embedding_features.py`: embedding geometry and adaptive clustering;
- `feature_schema.py`: stable ML feature namespaces;
- `semantic_context.py`: the retained short-identifier semantic features;
- `runners/`: stable extraction, cache, validation, and score materialization
  commands;
- `visual_features.py`: source-layout and token-position measurements.

## Chunk extraction

Java snippets are first parsed directly. Member fragments are retried inside a
synthetic enclosing class. Structurally truncated or non-Java snippets are
handled by the language-neutral lexical extractor. Missing parsers and invalid
feature/cache state raise explicit errors; the pipeline does not silently
substitute another embedding model or clustering family.

Extractor hygiene rules bound individual chunk strings and summarize large
array initializers so pathological snippets cannot dominate embedding work.
The retained chunk taxonomy includes identifiers, declarations, calls,
control-flow constructs, assignments, arithmetic, comparisons, logical and
bitwise expressions, literals, regular expressions, imports, unused imports,
and comments.

## Feature schema

Every dataset receives the same schema:

- **126 base features**: code size and layout, token and Halstead statistics,
  visual density and position, DFT summaries, chunk inventory and geometry,
  type-aware counts and ratios, identifier quality, and compression signals;
- **112 embedding-derived features per model**: coverage, semantic-context
  indicators, embedding geometry, and adaptive clustering summaries.

The embedding families are evaluated over four chunk views: `all`,
`only_identifier`, `semantic_core`, and `structural_core`. Clustering uses
OPTICS, HDBSCAN, automatically selected K-means, and automatically thresholded
agglomerative clustering. Fixed-radius DBSCAN sweeps, fixed-K sweeps, graph
features, `NORMAL`, and junk features are not part of the produced feature
tables.

ML-facing columns use explicit namespaces:

- `base__` for conventional, visual, chunk, type, and identifier features;
- `compression__` for compression features;
- `embedding__` for embedding geometry and clustering features;
- `semantic__` for short-identifier semantic-context features.

For one embedding model, the candidate table therefore contains 238 features
(126 base plus 112 model-specific features). Five-model consensus selection
runs five separate 238-feature screens; it does not concatenate all model
vectors into one enlarged training matrix.

## Supported embedding models

- `nomic-ai/nomic-embed-text-v1.5`
- `jinaai/jina-embeddings-v2-base-code`
- `Qwen/Qwen3-Embedding-0.6B`
- `Snowflake/snowflake-arctic-embed-m-v2.0`
- `voyageai/voyage-4-nano`

Each model has an independent cache under:

```text
artifacts/cognascore/embeddings/<embedding-model>/embeddings.sqlite
```

Download models explicitly when desired:

```bash
python -m src.methods.cognascore.runners.download_embedding_model \
  nomic-ai/nomic-embed-text-v1.5 \
  Qwen/Qwen3-Embedding-0.6B
```

## Stable production commands

Create or incrementally update embedding caches:

```bash
python -m src.methods.cognascore.runners.embeddings \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --device cpu \
  --batch-size 64 \
  --quiet
```

Create base feature tables:

```bash
python -m src.methods.cognascore.runners.features \
  datasets/scalabrino/dataset \
  --embedding-model nomic-ai/nomic-embed-text-v1.5
```

Create embedding-derived tables from an existing cache:

```bash
python -m src.methods.cognascore.runners.embedding_features \
  datasets/scalabrino/dataset \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --max-vectors-per-task 512 \
  --resume
```

Outputs are written to:

```text
artifacts/cognascore/features/base/<dataset>/<embedding-model>/features.csv
artifacts/cognascore/features/embedding/<dataset>/<embedding-model>/features.csv
```

Validate table schemas and the frozen ML feature list:

```bash
python -m src.methods.cognascore.runners.validate_feature_tables \
  --embedding-model nomic-ai/nomic-embed-text-v1.5
```

The repository-level scripts run the same process over all registered datasets
and all five embedding models:

```bash
bash scripts/refresh_cognascore_after_extractor_change.sh
REBUILD_EMBEDDING_FEATURES=0 bash scripts/rebuild_cognascore_feature_tables.sh
```

The second form above rebuilds base tables and validates existing
embedding-derived tables without rerunning embedding-feature computation.

## CognaScore ML

The stable materializer is:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

The current frozen configuration uses 30 selected features, Nomic feature
instantiations, `Ridge(alpha=200)`, and the five continuous-score datasets as
the final fit pool. JetBrains remains an external binary evaluation. It writes
predictions under:

```text
results/methods/cognascore_ml_consensus30/<dataset>/<embedding-model>/summary.json
```

The ranking and selection experiment that produced the frozen list lives in
`experiments/cognascore/consensus_selection.py`. Keeping it outside the stable
runner prevents a new exploratory selection from silently changing the
reported model.

## CognaScore Compact

The compact materializer is:

```bash
python -m src.methods.cognascore.runners.compact_formula
```

It retains a fixed four-feature linear formula and writes results under
`results/methods/cognascore_compact/`. Alternative compact-formula searches are research
experiments and live in `experiments/cognascore/compact_search.py`. Its default
run covers the six established datasets; either generated dataset can be added
explicitly with `--dataset` after its Qwen feature table has been materialized.
