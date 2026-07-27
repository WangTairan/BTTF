# CognaScore

CognaScore extracts Java lexeme-level signals, embeds each unique lexeme with a
local Hugging Face model, clusters embeddings with DBSCAN, and uses mean
within-cluster diameter as its score.

Java member snippets are parsed by falling back to a synthetic enclosing class
when they are not standalone compilation units. Structurally truncated or
non-Java fragments use a language-neutral lexical fallback so the same
chunk-embedding-clustering pipeline can cover CUDA, Java, and Python.

## Contents

- `method.py`: reusable scorer API.
- `extractors/python/`: active Java lexeme extractor based on `javalang`.
- `extractors/java/`: reference Java extractor retained from the original implementation.
- `embeddings.py`: local Nomic embedding stage.
- `embedding_cache.py`: SQLite-backed persistent embedding cache for reusable lexeme vectors.
- `embedding_features.py`: embedding-space geometry and clustering feature extraction.
- `clustering.py`: DBSCAN clustering and cluster diameter calculation.
- `visualization.py` and `templates/`: browsable output rendering.
- `feature_database.py`: stable feature-table extraction from CognaScore results.
- `runners/`: single-file and dataset commands.

## Defaults

- Embedding model: `nomic-ai/nomic-embed-text-v1.5`
- DBSCAN `eps`: `0.18`
- DBSCAN `min_pts`: `2`
- Embedding batch size: `32`
- Model cache directory: `models/`

## Commands

```bash
python -m src.methods.cognascore.runners.file
python -m src.methods.cognascore.runners.dataset datasets/mbjp_dev_dataset/readability_dataset.json --limit 1
python -m src.methods.cognascore.runners.dataset datasets/schnappinger --limit 1
python -m src.methods.cognascore.runners.dataset datasets/jetbrains --limit 1
python -m src.methods.cognascore.runners.dataset datasets/scalabrino/dataset --limit 1
```

Dedicated CognaScore runners also write an HTML cluster visualization. Results
are keyed by embedding model; changing DBSCAN parameters for the same model
overwrites that model's result directory, with the active parameters recorded
in `summary.json` or `manifest.json`.

```text
output/cognascore/<dataset>/<embedding-model>/
```

The Dorn dataset is supported through the language-neutral lexical fallback.
CLEAR is natural language and remains outside the code lexeme method's scope.

## Stable feature database

CognaScore can materialize a stable feature database after the normal dataset
run. The feature runner reads `output/cognascore/<dataset>/<model>/summary.json`
and writes a table that downstream training scripts can reuse without
rerunning embeddings or DBSCAN:

```bash
python -m src.methods.cognascore.runners.features datasets/scalabrino/dataset
python -m src.methods.cognascore.runners.features datasets/schnappinger
python -m src.methods.cognascore.runners.features datasets/dorn/dataset
python -m src.methods.cognascore.runners.features datasets/buse
python -m src.methods.cognascore.runners.features datasets/mbjp_dev_dataset/readability_dataset.json
python -m src.methods.cognascore.runners.features datasets/jetbrains
```

Output:

```text
output/cognascore_features/<dataset>/<embedding-model>/features.csv
output/cognascore_features/<dataset>/<embedding-model>/metadata.json
```

The first feature batch includes:

- identity columns: dataset, task id, and label when available;
- extractor hygiene: chunk lexemes longer than 256 normalized characters are
  discarded, and large array initializers are represented by compact summaries
  rather than full parser object strings;
- frozen formula features: generalized score, log vocabulary size, vocabulary size, and noise ratio;
- base CognaScore features: chunk count, cluster count, noise count, average cluster diameter, cluster size and diameter statistics, and per-chunk-type statistics;
- junk features: `JUNK` chunks are treated as extraction uncertainty rather
  than normal semantic chunk types, so they are reported through `junk_count`,
  `junk_ratio`, `junk_unique_ratio`, `junk_noise_ratio`, and
  `junk_cluster_count`;
- semantic chunk features: non-junk chunks are reported through
  `semantic_chunk_count`, `semantic_chunk_ratio`, and
  `semantic_noise_ratio`, while legacy `noise_ratio` is preserved for
  backward-compatible formula experiments;
- code features: LOC, line length, indentation, chunks per line, chunk size statistics, Halstead volume, token count, vocabulary size, and byte entropy.
- visual/layout features: line-length and indentation variation, indentation
  transitions, long-line and blank-line ratios, token-category densities,
  approximate token-category visual-area ratios, normalized vertical positions
  of identifiers/keywords/operators/member-access tokens, low-frequency DFT
  energy over line length, whitespace, identifier, keyword, and period/member
  access series, plus CognaScore chunk vertical dispersion and line-span
  features.

Use `--run-missing` only when the CognaScore summary is incomplete and missing
items should be computed on the fly.

## Persistent embedding cache

For experiments that need raw chunk embeddings, materialize them once into a
model-specific SQLite database:

```bash
python -m src.methods.cognascore.runners.embeddings --device cpu --batch-size 256 --quiet
```

Supported embedding models are:

- `nomic-ai/nomic-embed-text-v1.5` (default);
- `jinaai/jina-embeddings-v2-base-code`;
- `Qwen/Qwen3-Embedding-0.6B`.

Use `--embedding-model <model-name>` to materialize a separate cache for a
non-default model.

Download local model files before running a newly added embedding model:

```bash
python -m src.methods.cognascore.runners.download_embedding_model \
  jinaai/jina-embeddings-v2-base-code Qwen/Qwen3-Embedding-0.6B
```

Output:

```text
output/cognascore_embeddings/<embedding-model>/embeddings.sqlite
```

The cache is designed for adding more embedding models later. Each model has
its own directory and SQLite database. The database contains:

- `metadata`: schema version and model name;
- `embeddings`: one row per unique chunk text, keyed by SHA-256 text hash, with
  a `float32` vector blob;
- `sources`: dataset/task/chunk-type references for each cached text.

The runner is incremental: rerunning it only embeds missing texts. For bounded
runs, use `--max-new-embeddings N`; source references are still refreshed.
When the extractor changes, use `--replace-sources` for the selected datasets
so stale source references are removed before refreshed references are inserted:

```bash
python -m src.methods.cognascore.runners.embeddings datasets/schnappinger \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --device cpu \
  --batch-size 8 \
  --quiet \
  --replace-sources
```

## Embedding-derived feature database

The embedding cache can also be converted into a second stable feature table.
This table treats each task as a weighted set of cached chunk embeddings and
extracts geometry plus multiple clustering views. Algorithms with important
hyperparameters deliberately produce one feature family per setting:

```bash
python -m src.methods.cognascore.runners.embedding_features --max-vectors-per-task 512
```

For long runs, use resumable checkpointing:

```bash
python -m src.methods.cognascore.runners.embedding_features datasets/schnappinger \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --max-vectors-per-task 512 \
  --resume \
  --checkpoint-every 1
```

Use `--update-incomplete` with `--resume` to recompute only rows whose existing
coverage is below 1.0 or whose source count is 0. Use `--update-all` with
`--resume` after extractor or feature-definition changes; it recomputes every
selected task while checkpointing progress.

Output:

```text
output/cognascore_embedding_features/<dataset>/<embedding-model>/features.csv
output/cognascore_embedding_features/<dataset>/<embedding-model>/metadata.json
```

The current embedding-feature batch includes:

- coverage features: total chunk references, available embedded references,
  unique embedded chunk texts, coverage ratio, and the number of vectors passed
  to expensive algorithms after deterministic capping;
- embedding geometry: centroid norm, cosine distance to centroid, pairwise
  cosine distance, effective rank, and first-PC explained variance;
- auto-DBSCAN: `min_samples=max(2, round(log2(n_vectors)))` and `eps` from the
  0.75 quantile of the k-distance distribution, reporting cluster count, noise,
  size, diameter, chunk-type purity/entropy, mixed-cluster ratio, and
  control-flow-specific dispersion;
- KMeans sweeps: `k` in `2, 4, 8, 16`, reporting inertia, inertia per weight,
  largest cluster ratio, cluster-size CV, and silhouette;
- systematic chunk-view clustering features. For each chunk view, feature names
  use `<view>__<family>_<feature>`, for example
  `logic_core__hdbscan_noise_ratio` or `semantic_core__graph_component_count`.
  The first batch uses 20 views: all chunks, exclusions such as `no_junk` and
  `no_control_flow`, single-type views such as `only_identifier`, and grouped
  views such as `semantic_core`, `structural_core`, `logic_core`, `data_core`,
  `api_core`, and `nonsemantic_noise`. Each view runs embedding geometry,
  auto-DBSCAN, HDBSCAN, OPTICS, auto-KMeans, auto-agglomerative clustering, and
  adaptive graph connected components. The `hdbscan` package is a required
  dependency for this feature table; missing dependencies should fail loudly.

The schema is fixed across datasets. `embedding_coverage_ratio` should be used
when the embedding cache is incomplete; final experiments should first run the
embedding cache to completion and then regenerate these feature tables.

## Calibrated transfer experiments

Use the calibrated transfer runner for small-source training experiments that
should not mutate the main visualization outputs. It combines the stable base
and embedding feature tables, excludes model-output features such as
`base__generalized_score` by default, samples a small calibration set, selects
features by cross-validation on that calibration set, and reports all datasets:

```bash
python -m src.methods.cognascore.runners.calibrated_transfer \
  --feature-source combined \
  --train-dataset scalabrino \
  --train-size 60 \
  --features 20 \
  --alpha 100 \
  --label-bins 10 \
  --length-bins 3 \
  --length-feature base__loc
```

This runner is intended for clean ablations of sampling policy, feature count,
regularization, and whether length-stratified calibration improves transfer.
For upper-bound feature exploration, `--selection transfer_greedy` can optimize
named transfer datasets directly; those runs should be reported as exploratory
or development-selected, not as unbiased external transfer.

## Frozen two-feature generalization model

The interpretable generalization model uses only vocabulary breadth and the
CognaScore clustering noise ratio:

```text
score = 1.178590141
        - 0.187275298 * log(1 + vocabulary_size)
        + 0.200950211 * noise_ratio
```

The coefficients are frozen from Ridge (`alpha=30`) trained on 30 Scalabrino
items selected with NumPy seed 8734. Training labels are converted to within-set
percentile ranks. No target-dataset labels are used for fitting or calibration.
`generalized.generalized_readability_score` applies the frozen formula.

Cross-dataset results are Spearman correlations except JetBrains, which reports
MCC at the fixed 0.5 threshold and ROC AUC:

| Evaluation set | N | Result |
| --- | ---: | ---: |
| Scalabrino full | 200 | 0.592 |
| Scalabrino held out | 170 | 0.613 |
| Schnappinger | 304 | 0.595 |
| MBJP | 17 | 0.499 |
| Dorn | 360 | 0.383 |
| JetBrains | 119 | MCC 0.076 / AUC 0.575 |

These results measure transfer from Scalabrino, not within-dataset fitting.
The weaker Dorn and JetBrains results must not be presented as meeting the
0.6 continuous or 0.4 MCC targets.

## Supervised Ridge materialization

The current visualized CognaScore score is materialized by the supervised Ridge
runner:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

It trains Ridge on Scalabrino, Schnappinger, and Dorn using the selected
CognaScore/code-layout/visual-layout feature set, excludes stacked model-output
features such as `base__generalized_score`, and writes
`output/cognascore/<dataset>/<embedding-model>/summary.json`.

Use `feature_screen.py` and `calibrated_transfer.py` for feature-selection and
small-training-set ablations. The removed single-dataset validation-tuned ML
runner should not be used for reported results.
