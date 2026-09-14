# Research release

The repository release covers CognaScore and the source-interference tool.
The tool's package version is independent of the repository's Git tag.

## Verification

Run from the repository root with Python 3.11:

```bash
python -m pip install -r requirements-reproduction.txt
bash scripts/check_release.sh
git diff --check
git status --short
```

The checks cover documented Python command entry points, shell syntax,
extractor and feature regression tests, dataset-generation integration,
equal-weight benchmark averaging, and frozen-model checksums. They do not
call providers, download embedding models, or overwrite publication results.
The GitHub checks workflow runs the same suite on Linux.

Full evaluation requires local embedding and feature caches. Produce these
using the documented feature pipeline before running CV, LODO, or ablations.
Figure scripts use retained curve data, human annotations, or cached vectors;
they do not rerun feature selection. Regenerating the result site requires
local prediction reports and rewrites the tracked `docs/` directory.

## Files included in the release

- Source code, tests, installation files, and pipeline scripts.
- Dataset adapters and the formal human-rated and constructed datasets.
- The frozen 18-feature configuration, consensus-ranking evidence, and model
  artifacts, including `frozen_models/mi_convnet_cr/weights.pt`.
- Publication figure scripts/data and the tracked GitHub Pages site.

`artifacts/`, `results/`, downloaded `models/`, local manuscripts, credentials,
and virtual environments are not published. Their READMEs describe storage
and regeneration. Review any newly added file before staging it.

## Publication metadata

Before public distribution, add the repository license chosen by the authors
and citation metadata once the paper title and author list are finalized.
Check redistribution permissions for third-party datasets and released
baseline assets separately; a repository license does not replace their terms.

## Version marker

The current milestone is tagged `v1.0.0-embedding-only`. Here, "embedding-only"
distinguishes this route from future models using causal-LLM features: the
frozen predictor combines ten code-level features with eight embedding-derived
features. Auxiliary LLM-feature code remains available but is not part of this
18-feature model. Direct LLM scoring remains a comparison baseline.

The next major release will investigate adding LLM-derived features. Record the
commit identifier, frozen-model checksum, and paper/figure version in release
notes. Commit and annotated-tag creation are manual release steps.
