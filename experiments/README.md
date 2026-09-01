# Research experiments

This directory contains exploratory and paper-analysis code. Nothing here is
required to extract CognaScore features or apply a frozen CognaScore model.

- `cognascore/selection/`: feature screening and consensus ranking.
- `cognascore/evaluation/`: pooled CV, LODO, embedding-model refits, and
  controlled-interference evaluation.
- `cognascore/analysis/`: post-hoc feature-impact and annotation-reliability
  diagnostics.
- `cognascore/auxiliary/`: self-contained semantic-anchor and comment-threshold
  experiments.
- `cognascore/figures/`: publication-figure generation.
- `dorn/`: evaluation of the reconstructed Dorn baseline.

Stable dataset adapters remain in `src/datasets/`. Stable CognaScore feature
production and scoring commands remain in `src/methods/cognascore/`.
