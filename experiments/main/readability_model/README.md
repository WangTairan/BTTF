# Main readability-model experiments

This directory contains the primary model's retained configurations and
evaluation code. Production extraction and prediction live in
`src/methods/readability_model/`.

| Module | Role |
| --- | --- |
| `configs/` | Ordered feature sets and selection evidence |
| `selection/` | Candidate screening and documented validity probes |
| `evaluation/` | Pooled CV, leave-one-dataset-out, ablation, and controlled-interference evaluation |
| `figures/` | Research figures from saved screening/evaluation data |

The retained configurations are the final 11-feature model and the
independently selected 18-feature embedding-only predecessor. The six
human-rated datasets support selection, fitting, and benchmark evaluation;
the constructed Java/Python datasets provide controlled behavioral checks.

Run from the repository root:

```bash
python -m experiments.main.readability_model.evaluation.cross_validate_fixed
python -m experiments.main.readability_model.evaluation.leave_one_dataset_out
python -m experiments.main.readability_model.evaluation.ablate_final_representation \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json
python -m experiments.main.readability_model.evaluation.compare_embedding_model_refits
python -m experiments.main.readability_model.evaluation.compare_causal_lm_refits \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json
python -m experiments.main.readability_model.evaluation.bootstrap_benchmark_predictions \
  --pooled-predictions <pooled_predictions.csv> \
  --lodo-predictions <lodo_predictions.csv> \
  -o <output-directory>
```

Cached features and frozen models retain their historical `cognascore/`
namespace for provenance. Generated evaluations use
`results/experiments/readability_model/`. No evaluation script downloads
embedding weights or changes the pinned human-rated datasets.
