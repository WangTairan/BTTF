# Auxiliary semantic-feature experiments

This directory contains semantic-feature checks that do not use readability
labels and never refit the CognaScore readability model.

## Comment-to-code threshold stability

Each repetition draws 50 comment-bearing programs from the upper half of human
readability scores within each of the six datasets. Sampling is stratified,
with unavailable quota redistributed deterministically. A same-program
comment/code pair is a weak positive; a
comment borrowed from a different program in the same dataset is a weak
negative. Restricting mismatches to the same dataset prevents language or
dataset identity from making the negative task artificially easy.

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 \
  -m experiments.cognascore.auxiliary.comment_threshold_stability
```

The default experiment repeats the draw 200 times from base seed `20260828`.
It writes the per-repeat thresholds and every sampled pair. Same-program
pairing is explicitly treated as a reproducible proxy for relevance, not as a
replacement for human annotation.

Pass `--min-readability-percentile 0` to reproduce the unfiltered diagnostic.
The selected Nomic threshold is versioned in `comment_threshold.json`. The
constructed probe refuses to run if that value differs from the newly
generated stability median.

To probe both the handcrafted and resampled thresholds on 20 fixed groups from
the constructed non-informative-comment interference, run:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 \
  -m experiments.cognascore.auxiliary.comment_constructed_probe
```

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
