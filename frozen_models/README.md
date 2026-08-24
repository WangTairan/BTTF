# Frozen models

This directory contains small, publication-ready final model artifacts. Unlike
the rebuildable embedding caches and feature tables under `artifacts/`, these
files are intended to be versioned with the repository.

Each CognaScore model directory contains:

- `model.joblib`: the exact fitted scikit-learn pipeline;
- `model.json`: a portable manifest with the ordered feature list, preprocessing
  statistics, linear coefficients, intercept, training provenance, and fixed
  classification threshold.

Regenerate the current model with:

```bash
python -m src.methods.cognascore.runners.supervised_ridge
```
