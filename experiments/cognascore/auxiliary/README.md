# Auxiliary semantic-feature experiments

This directory contains semantic-feature checks that do not use readability
labels and never refit the CognaScore readability model.


## Reproducible mathematical/application anchors

The semantic-context corpus contains 48 frozen production-code units, balanced
across mathematical/application context and Python/Java.  It draws 12 units
from each of four repositories pinned to complete commit hashes: SymPy, Apache
Commons Math, Django, and Spring Petclinic.  No readability benchmark supplies
an anchor.

The committed manifest records the source revision, original path and lines,
archive SHA-256, snippet SHA-256, license, deterministic selection key, and the
complete eligibility rule.  The selected snippets are committed as experiment
inputs, so normal verification is offline:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 \
  -m experiments.cognascore.auxiliary.materialize_semantic_anchor_corpus
```

Re-materialization is an explicit audit operation. Download the four immutable
archives named in the manifest into `artifacts/cognascore/anchor_sources/`, then
run the same command with `--materialize`. Both archive and extracted-snippet
hash mismatches are fatal; there is no fallback or silent resampling.

Only the 48 frozen snippets need new vectors; the six benchmark caches are not
rebuilt. The following command verifies the corpus and fills only missing anchor
vectors for the five supported embedding models:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 \
  -m experiments.cognascore.auxiliary.embed_semantic_anchor_corpus \
  --device cpu
```

The sampled two-class gate is
`cos(code, mathematical centroid) - cos(code, application centroid)`. It has
no third weak-code class and therefore no `max` operation. Candidate-bearing
segments are averaged for long code.
