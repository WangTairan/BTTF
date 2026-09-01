# CognaScore: Code Readability Research Suite

This repository contains CognaScore and a reproducible evaluation suite for
code-readability research. CognaScore represents source code with typed
cognitive chunks, conventional code measurements, embedding-space geometry,
and adaptive clustering summaries.

The retained CognaScore model uses data-driven stability screening and a Ridge
predictor over 18 frozen features.

Comparison methods are isolated as separate method families, including RMC,
Posnett, Dorn, Scalabrino, direct LLM scoring, and the paper-aligned Mi
character-level CNN reproduction.

The tracked result site is published through GitHub Pages at
<https://wangtairan.github.io/Code-Readability/>.

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
Scalabrino, JetBrains, Dorn, and Schnappinger. Additional registered
datasets are retained as first-class evaluation datasets:

- `java_comparative_obfuscation`: 14 independently applied interference types
  paired with the same 100 original Java classes for fine-grained response
  analysis, including local data-flow and control-flow transformations.
- `python_comparative_degradation`: the same 14 independent interference
  categories applied to 100 production Python classes sampled equally from
  Django, Flask, Requests, and attrs.

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

Source references are atomically replaced by default. Existing vectors are
content-addressed and reused; vectors no longer referenced by any current task
may remain in SQLite but cannot enter a feature row. Embedding-derived tables
carry a build version, so the first run after an algorithm/schema change is a
full rebuild and an interrupted run resumes from its checkpoints.

If embeddings and source references are already current, rebuild feature
tables without recomputing vectors:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/rebuild_cognascore_feature_tables.sh
```

Use `BASE_ONLY=1` only when intentionally rebuilding the model-independent
tables while leaving the existing embedding-derived tables untouched.

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
`frozen_models/cognascore/consensus18_6dataset_sampled_margin_nomic/`. It includes the exact
serialized pipeline and a readable manifest containing the ordered features,
imputation and scaling values, Ridge parameters, and training-data hashes.
Its 18-feature list is fitted on the six continuous-score development datasets.

Research-only selection code is isolated under `experiments/cognascore/`.
The retained five-model consensus implementation can reproduce or extend the
selection analysis. Exploratory runs must use a separate output directory and
cannot overwrite the frozen scorer.

```bash
python -m experiments.cognascore.selection.consensus_selection \
  --select-top 30 --candidate-limit 220 \
  --c 0.08 --ridge-alpha 200 --stability-rounds 200 \
  --fit-dataset mbjp --fit-dataset buse --fit-dataset dorn \
  --fit-dataset scalabrino --fit-dataset schnappinger \
  --fit-dataset jetbrains \
  --final-embedding-model nomic-ai/nomic-embed-text-v1.5 \
  -o results/experiments/cognascore/selection_sandbox
```

This is a development experiment, not the production feature extractor. It
runs independent screens for the five embedding-model instantiations,
aggregates their canonical feature rankings, filters redundant candidates, and
fits the final Ridge model with one chosen embedding instantiation.

Materialize the retained scorer from existing feature tables:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```

The frozen ML runner fits one dataset-balanced model on MBJP, Buse, Dorn,
Scalabrino, Schnappinger, and the continuous JetBrains human-vote fraction,
then writes predictions for every registered report dataset. Selection
experiments remain separate so exploratory results cannot silently replace the
frozen scorer.

The retained Java and Python independent-interference evaluations are
reproduced together with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/run_constructed_variants_nomic.sh
```

After replacing or extending one constructed dataset, update only changed
source hashes with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/update_constructed_nomic_incremental.sh \
  datasets/constructed/java-comparative-obfuscation-class-100
```

The updater runs base extraction, source-reference/embedding maintenance, and
embedding-feature derivation sequentially. Unchanged source hashes reuse their
existing rows, while retired task IDs are removed from the rebuilt tables.

Run the locally supported comparison methods (Posnett transfer, Dorn, and
LOC) and produce their paired summaries with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/run_constructed_baselines.sh
```

The released Scalabrino implementation is excluded from this two-language
runner because its parser accepts Java only; its Java evaluation remains a
separate reproducible run. The API-based LLM baseline is also excluded from
this default evaluation.

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

Generate the normalized human-label distribution figure:

```bash
python figures/plot_readability_label_distributions.py
```

This figure uses each dataset's documented rating scale; JetBrains contributes
its readable-vote fraction rather than its majority-vote binary label.

## Reproducibility notes

- `artifacts/` contains rebuildable intermediate data and is ignored by Git.
- `results/` contains method and experiment results and is ignored by Git.
- `models/` contains downloaded model weights and is ignored by Git.
- `docs/` and `figures/` are publication artifacts and may be versioned.
- local paper PDFs under `bib/` are ignored; citation metadata may be tracked.
- commands fail on missing dependencies, incomplete caches, and schema
  mismatches rather than silently falling back.
