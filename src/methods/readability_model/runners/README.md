# Production runners

These command-line modules build and validate feature tables and fit/read the
retained predictors. Expensive embedding and LLM-feature generation is
checkpointed in `artifacts/`. Feature searches, probes, and ablations belong
under `experiments/`, not here.
