# Dorn (retrained)

This package provides a reproducible reconstruction of the feature-based model
from Dorn and Weimer, *A General Software Readability Model* (2012). It is not
an original pretrained Dorn artifact: none was released.

The reconstruction uses the 59 `Dorn-*` metrics in the public ARFF and the
compiled metric implementation released with Scalabrino et al.'s replication.
Metrics defined on fewer than 80% of the training rows are excluded so the
retrained model cannot exploit missingness from rarely applicable ratios.
Following the original high-level protocol, seven features are selected by a
forward wrapper evaluated with stratified 10-fold accuracy, and a logistic
regression is then fit on all 360 public Dorn rows. The internal wrapper score
is a selection objective, not an unbiased evaluation result. The readable-class
probability is exposed as the continuous score.

Train and freeze the reconstruction:

```bash
python -m src.methods.dorn.train
```

Evaluate it with the shared runner:

```bash
python -m src.experiments.evaluate_method datasets/scalabrino/dataset --method dorn
```

The implementation is deliberately labelled `Dorn (retrained)` so that results
cannot be mistaken for scores from an unavailable original binary or model.

Feature extraction uses a thin adapter over the compiled Dorn calculators in
the released `rsm.jar`. The adapter selects the declared Java, Python, or CUDA
analyzer and evaluates only the seven frozen features in a persistent JVM. It
does not reimplement or alter the formulas. This avoids the released
`ExtractMetrics` command's Java default and its unnecessary evaluation of the
other metric families.

The original snippet text is passed to these visual calculators unchanged. In
particular, Java fragments are not wrapped in a synthetic class, and original
line endings are preserved by the Dorn dataset adapter.
