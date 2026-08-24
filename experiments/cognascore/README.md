# CognaScore experiments

These modules reproduce model-development analyses while keeping the stable
feature pipeline small and difficult to misuse.

## Feature selection

- `feature_selection.py`: shared L1 stability-selection implementation.
- `consensus_selection.py`: five-embedding-model consensus selection followed
  by correlation filtering and Ridge fitting.
- `selection_sweep.py`: Top-K sensitivity sweeps for a single ranking.
- `compact_search.py`: constrained search for formulas with at most five
  features.
- `cross_validate_per_dataset.py`: independent within-dataset 5/10-fold CV.
- `cross_validate_pooled.py`: one pooled Ridge per fold over all six datasets.
- `leave_one_dataset_out.py`: train on five datasets and test on the sixth.

All three protocols use the same frozen 30-feature list. They deliberately do
not repeat feature selection inside the evaluation loop, and their metadata
records that limitation.

The current consensus experiment can be run with:

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

## Semantic-context probes

Exploratory tests for mathematical short-identifier context belong under
`semantic_context/`. The three currently materialized semantic-context
features remain in the stable feature schema so existing feature tables and
reported models do not change during this repository reorganization.

## Figures

`figures/plot_feature_count_sensitivity.py` generates the six-dataset PDF and
its CSV source data under the repository-level `figures/` directory.
