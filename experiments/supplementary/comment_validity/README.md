# Comment-feature validity checks

This directory contains the supplementary content-aware comment analysis
reported in the paper. It classifies comment spans into six deterministic,
label-independent content groups, aggregates their BPB from existing token-loss
traces, appends the resulting candidates to the original eligible pool, and
repeats the unchanged 15-pair stability screen.

`screen_comment_content_candidates.py` is the reproduction entry point.
`comment_content_groups.py` implements grouping and aggregation;
`comment_span_features.py` supplies shared span helpers. The experiment does
not perform new LM inference or use the controlled-interference datasets.
