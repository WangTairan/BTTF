# Research release checklist

This repository is a paper-reproduction package rather than an archive of all
development experiments.

## Verification

Run from the repository root with Python 3.11:

```bash
python -m pip install -r requirements-reproduction.txt
bash scripts/check_release.sh
git diff --check
git status --short
```

The checks cover documented Python entry points, shell syntax, extraction and
feature regression tests, controlled-dataset generation, equal-dataset
benchmark averaging, and frozen-model checksums. They do not call providers,
download pretrained weights, or overwrite saved publication outputs.

## Release contents

- the final 11-feature OpenCoder/Jina model and its 15-combination selection
  and robustness evidence;
- the independently selected 18-feature Jina embedding-only predecessor;
- all six human-rated datasets and both controlled-interference datasets;
- published/reproduced baselines and their frozen weights where applicable;
- feature-family ablation, bootstrap uncertainty, semantic-anchor, and
  content-aware comment analyses reported in the paper;
- the pinned recent-repository repair dataset and its validation tooling; and
- publication figure scripts, data, and rendered figures.

Superseded compact subset searches, obsolete reference instantiations, one-off
debugging probes, generated result pages, downloaded models, and local result
caches are excluded.

## Publication metadata

Before public distribution, add the chosen repository license and citation
metadata. Check redistribution terms for third-party datasets and baseline
assets separately. Record the commit identifier, frozen-model checksums, and
paper version in the release notes before creating an annotated tag.
