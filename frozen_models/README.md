# Frozen models

This directory contains versioned fitted predictors and their manifests.

Each CognaScore model directory contains:

- `model.joblib`: the exact fitted scikit-learn pipeline;
- `model.json`: a portable manifest with the ordered feature list, preprocessing
  statistics, linear coefficients, intercept, and training provenance.

The retained CognaScore publication model is
`cognascore/consensus18_6dataset_sampled_margin_nomic/`. The Dorn and Mi baseline
artifacts are retained in separate directories.

Refit and replace the CognaScore artifact from current feature tables:

```bash
python -m src.methods.cognascore.runners.supervised_ridge --overwrite-artifact
```

The command writes the fitted pipeline and an updated manifest. The canonical
configuration records the checksum used by the regression tests.
