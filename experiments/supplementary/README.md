# Supplementary experiments

This area holds experiments that test mechanisms or downstream behavior but
do not define or tune the main benchmark predictor.

- `semantic_anchors/` verifies the frozen mathematical/application reference
  corpus and its embeddings.
- `comment_validity/` reproduces the content-aware comment-feature diagnostic
  reported in the paper.
- Repository code-completion and repair experiments are implemented by
  `tools/source_interference/src/readability_experiments/` and documented in
  [that tool's README](../../tools/source_interference/README.md). Their local
  benchmark input is under `datasets/recent_repository_completion/`.

The six human-rated datasets remain the main training/evaluation pool; Java
and Python constructed interferences provide separate controlled checks.
