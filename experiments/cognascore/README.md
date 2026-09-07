# CognaScore experiments

This directory contains the reproducible analyses retained for the final
CognaScore release. Stable feature production and scoring remain under
`src/methods/cognascore/`; nothing here can silently replace the frozen model.

## Directory structure

- `evaluation/`: fixed-feature CV/LODO, ablations, five-model refits, and paired
  controlled-interference evaluation.
- `auxiliary/`: semantic-anchor corpus verification and embedding maintenance.
- `figures/`: rendering of retained publication curve data.
- `configs/`: the frozen feature list and selection evidence.

## Final model development

- `evaluation/cross_validate_fixed.py`: pooled grouped 10-fold evaluation of the frozen
  18-feature list.
- `evaluation/leave_one_dataset_out.py`: train on five datasets and evaluate on
  the sixth.
- `evaluation/ablate_final_model.py`: remove the code-level or complete
  embedding-derived family, or independently remove the embedding-geometry or
  clustering subfamily, without reselection, and rerun the canonical pooled
  10-fold, LODO, and held-out Java/Python controlled-interference protocols.
- `evaluation/compare_embedding_model_refits.py`: independently refit the same
  18-feature Ridge for all five embedding models and compare coefficients,
  pooled CV, LODO, and controlled-interference responses.
- `configs/consensus18_6dataset_sampled_margin.json`: canonical ordered feature
  list used by the publication model.

The feature list is fixed before the CV and LODO scripts run. Their output
metadata explicitly records that selection is not repeated inside each fold.
Whenever benchmark results are summarized across datasets, the six
dataset-specific correlations are averaged with equal weight, matching the
main benchmark table. Controlled-interference results instead pool all changed
pairs directly and do not average category-level percentages.
The final-model group ablation can be reproduced with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  python3 \
  -m experiments.cognascore.evaluation.ablate_final_model
```

Exploratory selection, feature-addition/replacement searches, post-hoc analyses,
and comment-threshold probes have been removed. The frozen feature list and
ranking evidence remain in `configs/`. All four causal-LM surprisal features
and their production pipeline remain under `src/methods/cognascore/`.

## Controlled experiments

`evaluation/evaluate_constructed_variants.py` performs independent, paired interference
tests for both the Java and Python constructed datasets. Every transformed
class is compared with the same original, and inapplicable unchanged variants
are separated from changed-pair response rates. Overall results pool all
changed pairs directly; categories are retained only as diagnostic breakdowns
and are never averaged with equal category weights. Rebuild Nomic features and
evaluate both datasets sequentially with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/run_constructed_variants_nomic.sh
```

For an updated single constructed dataset, use the hash-aware incremental
pipeline:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
  bash scripts/update_constructed_nomic_incremental.sh \
  datasets/constructed/java-comparative-obfuscation-class-100
```

## Figures and semantic anchors

- `figures/plot_feature_count_sensitivity.py`: render the retained CSV curve;
  no feature search or model refitting is performed.
- `auxiliary/materialize_semantic_anchor_corpus.py`: verify or rebuild the frozen corpus.
- `auxiliary/embed_semantic_anchor_corpus.py`: fill missing anchor embeddings.

Generated outputs belong under `results/experiments/cognascore/`; final
method artifacts belong under `frozen_models/`.
