# Experiments

Shared experiment orchestration lives in this package. Metric
implementations belong in `src/methods/`, method-specific CLIs belong in each
method package's `runners/`, and dataset parsing belongs in `src/datasets/`.

Default output paths are generated consistently:

```text
results/methods/<method>/<dataset>/<config-if-needed>/
```

For example, method evaluations produce:

```text
results/methods/posnett/dorn/
results/methods/scalabrino/scalabrino/
results/methods/llm_prompt/scalabrino/<model>/
```

Passing `-o <root>` replaces `results/methods` while retaining this layout.

Dataset keys, comparison-method output names, and overwrite/history policy are
registered in `src/experiments/registry.py`. Deterministic comparison methods
use stable paths and overwrite summaries on rerun; LLM and RMC configurations
remain traceable. CognaScore's frozen materializers are maintained by its own
stable runners, while model-development code lives under `experiments/`.

Binary datasets are evaluated with best-threshold MCC. Continuous datasets are
evaluated with Spearman correlation.
