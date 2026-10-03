# Published display measurements

Each compressed JSON file corresponds to one registered dataset. It contains
sample identities and source hashes, the final model's 11 measured features,
source-linked regions, and baseline scores and feature-panel inputs.

The viewer recomputes BTTF contributions with the frozen model. Original
source code remains in `datasets/`; cloud responses remain in
`results/direct_llm/`. No model checkpoints, raw subprocess output, temporary
file names, or local paths are included here.

These files support browsing the published results without regenerating
feature tables. Full CV, LODO, selection, and ablation experiments use the
reproduction commands documented in the root README.
