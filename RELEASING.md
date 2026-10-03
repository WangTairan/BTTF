# Research release checklist

This repository is a paper-reproduction package rather than an archive of all
development experiments.

## Verification

Run from the repository root with Python 3.11:

```bash
python -m pip install -r requirements/reproduction.txt
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
- all six human-rated dataset indexes and results, both controlled-interference
  datasets, and source collections whose redistribution terms are identified;
- published/reproduced baselines and their frozen weights where applicable;
- the per-sample records from all three runs of each direct-LLM baseline;
- feature-family ablation, bootstrap uncertainty, semantic-anchor, and
  content-aware comment analyses reported in the paper;
- publication figure scripts, data, and rendered figures.
- the interactive viewer, its frontend assets, and source-matched display
  measurements that work without development caches.

Superseded compact subset searches, obsolete reference instantiations, one-off
debugging probes, generated result pages, SVN metadata, downloaded models, and local result
caches are excluded.

## Publication metadata

Citation metadata is in `CITATION.cff`; a license for the original code
remains to be selected.
Check redistribution terms for third-party datasets and baseline assets
separately, using `THIRD_PARTY.md`. Record the commit identifier, frozen-model checksums, and
paper version in the release notes before creating an annotated tag.

Identified third-party license texts and attribution notices are bundled under
`licenses/third_party/` and the corresponding data directories. The Schnappinger
benchmark contains only label-referenced sources and original notices, not
upstream binaries or documents. Explicit redistribution terms for Buse, Dorn,
Scalabrino source data and the Scalabrino tool remain to be confirmed.
The three complete source collections are excluded from new public release
contents under the separate "redistribution permission pending" category in
`THIRD_PARTY.md`. Their local files remain available for reproduction. The
viewer retains all scores and entries without those complete collections;
the fixed 30-case excerpts and recorded LLM replies remain unchanged.

Before tagging, verify a fresh checkout without ignored caches as well as the
development checkout. The viewer's bundled display data are not replacements
for regenerating features or rerunning the benchmark protocols.
