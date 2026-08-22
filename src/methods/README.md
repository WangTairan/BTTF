# Methods

Stable readability methods and their materialization runners live here:

- `cognascore/`: typed cognitive chunks, conventional code features,
  embedding geometry, adaptive clustering, CognaScore ML, and CognaScore
  Compact;
- `rmc/`: Recursive Masking Complexity and its dataset runners;
- `posnett/`: the deterministic Posnett readability formula;
- `scalabrino/`: wrapper around the released Scalabrino implementation;
- `llm_prompt/`: direct LLM readability scoring baseline;
- `loc_baseline/`: lines-of-code baseline.

All comparison methods are kept separate from CognaScore. Exploratory feature
selection, sweeps, probes, and ablations belong under `experiments/`, not in a
method package's stable runner directory.
