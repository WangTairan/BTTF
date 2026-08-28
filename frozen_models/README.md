# Frozen models

This directory contains small, publication-ready final model artifacts. Unlike
the rebuildable embedding caches and feature tables under `artifacts/`, these
files are intended to be versioned with the repository.

Each CognaScore model directory contains:

- `model.joblib`: the exact fitted scikit-learn pipeline;
- `model.json`: a portable manifest with the ordered feature list, preprocessing
  statistics, linear coefficients, intercept, training provenance, and fixed
  classification threshold.

Only the publication model
`cognascore/consensus18_6dataset_sampled_margin_nomic/` is retained. Regenerate it
with:

```bash
python -m src.methods.cognascore.runners.supervised_ridge --overwrite-artifact
```
