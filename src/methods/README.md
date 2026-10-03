# Methods

The primary method is [`readability_model/`](readability_model/): code-level,
embedding-derived, and causal-LM feature construction plus fixed Ridge scoring.

Comparison methods are independent implementations:

- [`posnett/`](posnett/) and [`lloc_baseline/`](lloc_baseline/): fixed formulas;
- [`scalabrino/`](scalabrino/) and [`dorn/`](dorn/): released-tool wrappers or
  paper-aligned reconstruction;
- [`mi_convnet_cr/`](mi_convnet_cr/): reconstructed character CNN;
- [`llm_prompt/`](llm_prompt/): direct API scoring.

Each method has its own README. Feature screening and benchmark evaluation
belong under `experiments/`, not inside a production method package.
