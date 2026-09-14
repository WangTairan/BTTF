# CognaScore

A research toolkit for code readability. CognaScore combines typed code chunks,
code-level measurements, embedding geometry, and adaptive clustering in a
fixed 18-feature Ridge model. The repository also includes comparison methods,
independent Java/Python interference datasets, and reproducible evaluations.

The `v1.0.0-embedding-only` milestone freezes the code-level and embedding-derived
18-feature model; causal-LLM features remain auxiliary experiments for the next
major version.

[Interactive results](https://wangtairan.github.io/Code-Readability/)

## Repository layout

```text
src/datasets/               Dataset adapters
src/methods/                CognaScore and comparison methods
src/experiments/            Shared evaluation runners and metrics
src/site/                   Result-site generator
experiments/cognascore/     Model configuration, ranking evidence, and evaluation
experiments/dorn/           Dorn baseline evaluation
tools/source_interference/ Java/Python dataset generation and downstream tasks
datasets/                  Human-rated and constructed datasets
frozen_models/             Fitted predictors and manifests
figures/                   Paper figures and plotting scripts
scripts/                   Pipeline and maintenance commands
docs/                      GitHub Pages result site
artifacts/                 Source corpora, embeddings, features, and caches
results/                   Predictions and experiment reports
models/                    Downloaded model weights
```

## Installation

Use Python 3.11 and run commands from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

To match the statistical-library versions recorded by the frozen model, use
`python -m pip install -r requirements-reproduction.txt` instead.

The requirements include an editable installation of the source-interference
tool. Model weights, source checkouts, and generated caches are stored locally
and excluded from Git.

The released Scalabrino and Dorn feature implementations also require a JDK
with `java` and `javac` available on `PATH`. LLM runners require provider credentials.

## Datasets and methods

The six human-rated datasets are MBJP, Buse, Scalabrino, Dorn, Schnappinger,
and JetBrains. The two constructed datasets contain independent interferences
applied to Java and Python classes. Dataset paths, targets, and evaluation
metrics are listed in [datasets/README.md](datasets/README.md).

Comparison methods include Posnett, Scalabrino, the reconstructed Dorn model,
the Mi ConvNetCR reproduction, direct LLM scoring, LOC, and RMC. Each method
has its own implementation and README under `src/methods/`.

## Feature production

The pipeline extracts code-level features, caches chunk embeddings, and derives
embedding geometry and adaptive-clustering features. Embedding vectors are
content-addressed; incremental updates reuse existing vectors and completed
feature rows. Schema and build versions control feature-table rebuilds.

Download model weights before the first embedding run:

```bash
python -m src.methods.cognascore.runners.download_embedding_model
```

Refresh source references and update all five models on the six human-rated
datasets, plus Nomic on the constructed datasets:

```bash
bash scripts/refresh_cognascore_after_extractor_change.sh
```

Rebuild feature tables from current embedding caches:

```bash
bash scripts/rebuild_cognascore_feature_tables.sh
```

For the full five-model comparison, include both constructed datasets:

```bash
INCLUDE_CONSTRUCTED_ALL_MODELS=1 bash scripts/refresh_cognascore_after_extractor_change.sh
```

This remains sequential and reuses cached vectors. Set the same flag on the
rebuild script when only feature tables need updating.

Validate existing tables:

```bash
python -m src.methods.cognascore.runners.validate_feature_tables \
  --embedding-model nomic-ai/nomic-embed-text-v1.5
```

[CognaScore documentation](src/methods/cognascore/README.md) describes the
feature schema, supported models, and individual runners.

## Model and evaluation

The frozen model is in
`frozen_models/cognascore/consensus18_6dataset_sampled_margin_nomic/`.
Its manifest records the ordered features, preprocessing, coefficients,
software versions, and provenance.

Evaluate the fixed feature schema using pooled 10-fold CV, LODO, ablations,
and independent fits for the five embedding models:

```bash
python -m experiments.cognascore.evaluation.cross_validate_fixed
python -m experiments.cognascore.evaluation.leave_one_dataset_out
python -m experiments.cognascore.evaluation.ablate_final_model
python -m experiments.cognascore.evaluation.compare_embedding_model_refits
```

The six dataset-specific Spearman correlations receive equal weight in
benchmark averages. Interference response rates pool changed original–variant
pairs directly. Each evaluation records its training datasets and protocol.

Fit the fixed schema and write predictions with:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

Replacing an existing fitted artifact requires `--overwrite-artifact`.

## Constructed datasets

Update only changed source hashes for one dataset:

```bash
bash scripts/update_constructed_nomic_incremental.sh \
  datasets/constructed/java-comparative-obfuscation-class-100
```

Update and evaluate both datasets sequentially:

```bash
bash scripts/run_constructed_variants_nomic.sh
bash scripts/run_constructed_baselines.sh
```

Generate separate reproduction copies from local source corpora:

```bash
bash scripts/generate_constructed_datasets.sh
```

Generation writes to `artifacts/source_interference/reproductions/` by default.
Source requirements, interference definitions, and downstream-task commands
are in [the tool documentation](tools/source_interference/README.md).

## Figures and result site

```bash
python -m experiments.cognascore.figures.plot_feature_count_sensitivity
python figures/plot_readability_label_distributions.py
python figures/plot_chunk_clustering_motivation.py
python -m src.site.build
```

## Maintenance

```bash
bash scripts/check_release.sh
```

The check runs compilation, shell syntax checks, regression tests, and
frozen-model checksum verification. It does not rebuild datasets or embeddings.
Auxiliary semantic-anchor and causal-LM feature tools remain available under
`experiments/cognascore/auxiliary/` and `src/methods/cognascore/`.

See [RELEASING.md](RELEASING.md) for the release checklist and artifact boundaries.
