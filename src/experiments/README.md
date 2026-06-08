# Experiments

Shared experiment orchestration lives in this package. Metric
implementations belong in `src/methods/`, method-specific CLIs belong in each
method package's `runners/`, and dataset parsing belongs in `src/datasets/`.

Default output paths are generated consistently:

```text
output/<method>/<dataset>/<config-if-needed>/
```

For example, method evaluations produce:

```text
output/posnett/dorn/
output/scalabrino/scalabrino/
output/cognascore/scalabrino/nomic-ai-nomic-embed-text-v1.5/
```

Passing `-o <root>` replaces `output` while retaining this layout.

Dataset keys, method output names, and overwrite/history policy are registered
in `src/experiments/registry.py`. Deterministic readability methods use stable
paths and overwrite summaries on rerun; CognaScore, LLM-prompt, and RMC use
configuration-specific paths so experimental variants remain traceable.

Binary datasets are evaluated with best-threshold MCC. Continuous datasets are
evaluated with Spearman correlation.
