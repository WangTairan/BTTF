# Code Readability Prediction

Reproduction package for an interpretable code-readability model built from
traditional code measurements, embedding-space organization, and causal-LM
predictability. The repository contains the frozen models, datasets, selection
evidence, evaluation code, controlled transformations, and figure sources used
in the paper.

## Repository map

| Location | Contents |
| --- | --- |
| [`src/methods/readability_model/`](src/methods/readability_model/) | Feature extraction and Ridge prediction |
| [`experiments/main/readability_model/`](experiments/main/readability_model/) | Selection, benchmark evaluation, robustness, ablation, and uncertainty analyses |
| [`experiments/baselines/`](experiments/baselines/) | Published and reproduced comparison methods |
| [`experiments/supplementary/`](experiments/supplementary/) | Paper-reported semantic-anchor and comment diagnostics |
| [`tools/source_interference/`](tools/source_interference/) | Controlled Java/Python transformations and the repair probe |
| [`datasets/`](datasets/) | Human-rated, controlled-interference, and pinned repair datasets |
| [`frozen_models/`](frozen_models/) | Final 11-feature model, 18-feature predecessor, and fitted baselines |
| [`figures/`](figures/) | Publication figures, plotting scripts, and retained plotting data |

The reference final model uses OpenCoder-1.5B-Base predictability features and
Jina Embeddings v2 Base Code. The separately selected 18-feature
embedding-only predecessor also uses Jina. Historical artifact directories
retain the `cognascore/` namespace solely to preserve provenance.

## Setup

Use Python 3.11 from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-reproduction.txt
```

Install `requirements-llm.txt` only when regenerating causal-LM feature tables.
Some baselines require a JDK, and the direct-LLM baseline requires provider
credentials. Installation and release checks do not call external APIs.

## Verify the release

```bash
bash scripts/check_release.sh
git diff --check
```

This verifies imports, documented commands, feature contracts, dataset tools,
and frozen-model checksums without downloading model weights or overwriting
publication results.

## Reproduce the main analyses

```bash
python -m experiments.main.readability_model.evaluation.cross_validate_fixed \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.leave_one_dataset_out \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.ablate_final_representation \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.evaluate_constructed_variants
```

These evaluations require locally generated feature tables under `artifacts/`.
Generation is documented in the [method README](src/methods/readability_model/README.md).
Dataset provenance and immutable inputs are documented in
[`datasets/README.md`](datasets/README.md).

The repair-probe input is archived under
[`datasets/recent_repository_completion/`](datasets/recent_repository_completion/pytest_python/README.md)
and can be verified without fetching its upstream repository:

```bash
python scripts/local_recent_completion_dataset.py verify
```

Generated caches, downloaded weights, and complete result directories are not
tracked. Compact-model searches, obsolete intermediate feature budgets,
debugging probes, and the former result website are intentionally excluded
from this reproduction release.
