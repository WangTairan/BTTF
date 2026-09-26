# Frozen models

This directory contains the fitted predictors needed to reproduce the paper.
Each primary model directory contains `model.joblib` and a portable
`model.json` manifest with feature order, preprocessing statistics,
coefficients, training provenance, and the serialized-model checksum.

Primary artifacts retain the historical `cognascore/` storage namespace:

- `consensus11_6dataset_three_llm_opencoder_jina/`: final 11-feature model,
  using OpenCoder-1.5B-Base and Jina Embeddings v2 Base Code;
- `consensus18_6dataset_sampled_margin_jina/`: independently selected
  18-feature embedding-only predecessor using Jina; and
- `dorn_retrained/` and `mi_convnet_cr/`: fitted comparison methods.

The corresponding feature specifications and selection evidence are under
`experiments/main/readability_model/configs/`. Obsolete 23-feature, compact,
and superseded reference instantiations are not part of the release.
