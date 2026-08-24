# CognaScore: Code Readability Research Suite

This repository contains CognaScore and a reproducible evaluation suite for
code-readability research. CognaScore represents source code with typed
cognitive chunks, conventional code measurements, embedding-space geometry,
and adaptive clustering summaries.

Two CognaScore routes are retained:

- **CognaScore ML** uses data-driven stability screening and a Ridge model. The
  frozen development model uses 30 features.
- **CognaScore Compact** is restricted to at most five features and exposes a
  short linear formula.

The comparison implementations are retained unchanged as separate method
families: RMC, Posnett, Scalabrino, and direct LLM scoring.

## Repository structure

```text
datasets/              Input datasets and dataset-specific notes
experiments/           Model-development and paper-analysis scripts
figures/               Reproducible paper figures and their source data
scripts/               End-to-end maintenance commands
src/datasets/          Stable dataset adapters
src/experiments/       Shared evaluation, metrics, paths, and registry
src/methods/           Stable method and feature-production code
src/site/              Static result-site generator
docs/                  Generated, tracked result site
artifacts/             Rebuildable embedding and feature caches
results/               Method results and experiment analyses
models/                Downloaded third-party model weights
bib/local_papers/      Local reading copies of papers (ignored by Git)
```

Reusable data loading, feature production, and frozen scoring live under
`src/`; feature selection, sweeps, ablations, and paper-figure generation live
under `experiments/`.

## Installation

Python 3.11 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Embedding models are downloaded to `models/` on first use or through the
CognaScore download runner. Generated vectors live under `artifacts/`, not
beside the model weights. Large artifacts and results are intentionally not
versioned.

## Datasets

The six established development/evaluation datasets are MBJP, Buse,
Scalabrino, JetBrains, Dorn, and Schnappinger. Two additional registered
datasets are retained as first-class evaluation datasets:

- `generated_readability_90`: 90 generated Java examples with low, normal, or
  high readability instructions.
- `java_progressive_obfuscation`: 100 Java classes with complete L0--L6
  cumulative obfuscation chains for grouped trend evaluation.

Their canonical paths, labels, metrics, and reconstruction command are
documented in [`datasets/README.md`](datasets/README.md). Dataset adapters
return a common `DatasetItem` representation and are registered in
[`src/experiments/registry.py`](src/experiments/registry.py).

## CognaScore pipeline

The stable feature pipeline has three persistent stages:

1. extract base, visual, chunk, type-inventory, and compression features;
2. cache chunk embeddings once per embedding model;
3. derive embedding-geometry and adaptive-clustering tables from the cache.

To refresh sources after changing the extractor, then rebuild and validate all
five embedding-model feature tables, run:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/refresh_cognascore_after_extractor_change.sh
```

If embeddings and source references are already current, rebuild feature
tables without recomputing vectors:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  REBUILD_EMBEDDING_FEATURES=0 \
  bash scripts/rebuild_cognascore_feature_tables.sh
```

Validate existing tables directly:

```bash
python -m src.methods.cognascore.runners.validate_feature_tables \
  --embedding-model nomic-ai/nomic-embed-text-v1.5
```

See [`src/methods/cognascore/README.md`](src/methods/cognascore/README.md) for
the feature schema and stable runners.

## Model development and frozen scores

Materialize the final CognaScore ML model and all report datasets:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

The complete frozen model is written under
`frozen_models/cognascore/consensus30_5continuous_nomic/`. It includes the exact
serialized pipeline and a readable manifest containing the ordered features,
imputation and scaling values, Ridge parameters, training-data hashes, and the
fixed classification threshold learned from the five continuous-score datasets.

Research-only selection code is isolated under `experiments/cognascore/`.
The current five-model consensus experiment is invoked as:

```bash
python -m experiments.cognascore.consensus_selection \
  --select-top 30 \
  --candidate-limit 220 \
  --c 0.08 \
  --ridge-alpha 200 \
  --stability-rounds 200 \
  --fit-dataset mbjp --fit-dataset buse --fit-dataset dorn \
  --fit-dataset scalabrino --fit-dataset schnappinger \
  --final-embedding-model nomic-ai/nomic-embed-text-v1.5 \
  -o results/experiments/cognascore/consensus_k30_fit_5continuous
```

This is a development experiment, not the production feature extractor. It
runs independent screens for the five embedding-model instantiations,
aggregates their canonical feature rankings, filters redundant candidates, and
fits the final Ridge model with one chosen embedding instantiation.

Materialize the retained scoring routes from existing feature tables:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
python -m src.methods.cognascore.runners.compact_formula
```

The frozen ML runner fits its reported model on Buse, Dorn, and Scalabrino and
writes predictions for all registered report datasets. Selection experiments
and their outputs remain separate so exploratory results cannot silently
replace the frozen scorer.

## Comparison methods

The shared evaluator supports deterministic and direct-scoring comparison
methods:

```bash
python -m src.experiments.evaluate_method \
  datasets/scalabrino/dataset --method posnett

python -m src.experiments.evaluate_method \
  datasets/scalabrino/dataset --method scalabrino
```

Method-specific instructions are in [`src/methods/README.md`](src/methods/README.md).

## Result site and paper figures

Generate the tracked result site:

```bash
python -m src.site.build
```

Generate the six-dataset feature-count sensitivity figure:

```bash
python -m experiments.cognascore.figures.plot_feature_count_sensitivity
```

The script writes both the PDF and its plotted CSV data to `figures/`.

## Reproducibility notes

- `artifacts/` contains rebuildable intermediate data and is ignored by Git.
- `results/` contains method and experiment results and is ignored by Git.
- `models/` contains downloaded model weights and is ignored by Git.
- `docs/` and `figures/` are publication artifacts and may be versioned.
- local paper PDFs under `bib/` are ignored; citation metadata may be tracked.
- commands fail on missing dependencies, incomplete caches, and schema
  mismatches rather than silently falling back.
