# CognaScore experiments

This directory contains the reproducible analyses retained for the final
CognaScore release. Stable feature production and scoring remain under
`src/methods/cognascore/`; nothing here can silently replace the frozen model.

## Final model development

- `feature_selection.py`: L1 stability screening shared by selection tools.
- `selection_policy.py`: deterministic exclusions for invalid or discarded
  candidate features.
- `consensus_selection.py`: five-embedding-model consensus ranking,
  correlation filtering, and Ridge fitting.
- `cross_validate_fixed.py`: pooled grouped 10-fold evaluation of the frozen
  18-feature list.
- `leave_one_dataset_out.py`: train on five datasets and evaluate on the sixth.
- `configs/consensus18_6dataset_sampled_margin.json`: canonical ordered feature
  list used by the publication model.

The feature list is fixed before the CV and LODO scripts run. Their output
metadata explicitly records that selection is not repeated inside each fold.
The production tables retain 194 candidates per embedding-model instantiation.
Before stability screening, `selection_policy.py` excludes 13 theory-rejected
features: three unstable/redundant cluster-size variability measurements and
ten absolute vertical-position measurements. The resulting 181 candidates are
ranked; retaining the excluded columns supports transparent appendix reporting
and ablation without allowing them into the formal model-selection procedure.

## Controlled experiments

Two constructed Java experiments are retained:

- `evaluate_progressive_obfuscation.py`: grouped L0--L6 cumulative degradation
  trajectories;
- `evaluate_constructed_variants.py`: independent, paired interference tests
  against the same original classes.

`compare_progressive_obfuscation.py` and the two feature-analysis modules
provide supporting diagnostics. Rebuild features and evaluate both datasets
sequentially with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/run_constructed_variants_nomic.sh
```

## Compact route and figures

- `compact_search.py`: optional research search for formulas restricted to at
  most five features. The existing Compact scorer is unchanged.
- `figures/plot_feature_count_sensitivity.py`: publication feature-count
  sensitivity figure.
- `analyze_human_rating_reliability.py`: human-rating agreement diagnostics.
- `auxiliary/comment_threshold_stability.py`: repeated, six-dataset validation
  of the model-specific comment-to-code threshold without readability labels.

Generated outputs belong under `results/experiments/cognascore/`; only final
method artifacts belong under `frozen_models/`.
