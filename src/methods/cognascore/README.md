# CognaScore

CognaScore is the repository's active code-readability feature pipeline. It
extracts typed cognitive chunks, measures conventional and visual code
properties, embeds selected chunk views, and summarizes embedding geometry and
adaptive cluster structure.

The retained CognaScore model is a Ridge predictor over 18 frozen features.

Feature selection and ablation code is intentionally outside this package in
`experiments/cognascore/selection/` and `experiments/cognascore/evaluation/`.

## Package structure

- `extractors/java/`: javalang-based Java extraction with bounded member,
  method-body, and lexical handling for incomplete snippets;
- `extractors/c_like.py`: explicit language-neutral lexical extraction for C,
  C++, and CUDA without passing those languages through the Java parser;
- `extractors/python_ast.py`: strict Python AST and tokenizer extraction;
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
synthetic enclosing class, and structurally truncated Java snippets use the
bounded lexical path. C, C++, and CUDA always use the explicit C-like lexical
extractor and are never passed to the Java parser. Missing parsers and invalid
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

- **95 base features**: code size and layout, token and Halstead statistics,
  visual density and position, DFT summaries, chunk inventory and geometry,
  type-aware counts and ratios, identifier quality, and compression signals;
- **102 embedding-derived features per model**: coverage, semantic-context
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

Five-model consensus selection runs five separate screens over the same
canonical feature names; it does not concatenate model-specific columns into
one enlarged training matrix. Exact feature counts are recorded in generated
table metadata so documentation cannot drift when the candidate schema changes.

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

The embedding runner also materializes a versioned, benchmark-independent
comment-relevance calibration set. Before feature extraction, each embedding
model deterministically learns its own comment/code similarity threshold by
maximizing balanced accuracy on these calibration anchors. The resulting
artifact is stored at:

```text
artifacts/cognascore/calibration/<embedding-model>/comment_relevance.json
```

The threshold is never fitted on a readability benchmark. Each comment is
aligned to its most similar non-comment semantic chunk, since a local comment
need not describe an entire class. Four features summarize these alignments:
their mean and minimum, the fraction below the calibrated threshold, and the
mean similarity deficit.
Feature extraction fails loudly when the calibration embeddings are missing.

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
bash scripts/rebuild_cognascore_feature_tables.sh
```

The refresh command atomically replaces the selected datasets' source
references while retaining reusable text-keyed vectors. The feature builder
uses a versioned, checkpointed rebuild: old build versions are recomputed, and
restarting an interrupted current-version run reuses completed rows.

The second form rebuilds all feature tables from existing vector caches without
running an embedding model. Set `BASE_ONLY=1` only for an intentional base-only
refresh.

## CognaScore ML

The stable materializer is:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

The current frozen configuration uses 18 selected features, Nomic feature
instantiations, `Ridge(alpha=200)`, and all six continuous-score datasets as
the final fit pool. It writes
predictions under:

```text
results/methods/cognascore_ml_consensus18_6dataset_sampled_margin/<dataset>/<embedding-model>/summary.json
```

The ranking and selection experiment that produced the frozen list lives in
`experiments/cognascore/selection/consensus_selection.py`. Keeping it outside the stable
runner prevents a new exploratory selection from silently changing the
reported model.
