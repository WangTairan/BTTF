# Retained research experiments

Stable feature production and scoring remain under `src/`.

- `cognascore/evaluation/`: fixed-feature CV, LODO, ablations, embedding-model refits, and controlled-interference evaluation.
- `cognascore/configs/`: frozen feature configuration and ranking evidence.
- `cognascore/auxiliary/`: semantic-anchor corpus verification and embedding maintenance.
- `cognascore/figures/`: rendering of retained publication curve data.
- `dorn/`: evaluation of the reconstructed Dorn baseline.

Exploratory screening, feature-addition/replacement searches, post-hoc analysis,
and comment-threshold probes have been removed. The four causal-LM features,
their extraction runner, tests, and cached tables are retained.
