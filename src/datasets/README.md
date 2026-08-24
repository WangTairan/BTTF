# Dataset Adapters

Dataset-specific parsing lives here, separately from metric execution:

- `mbjp/`: MBJP JSON code dataset.
- `code_jsonl/`: shared adapter for code JSONL datasets.
- `scalabrino/`: original Scalabrino dataset adapter reading `scores.csv` and
  `Snippets/*.jsnp` directly.
- `dorn/`: original Dorn dataset adapter reading `scores/*.csv` and
  `snippets/<language>/*.jsnp` directly.
- `schnappinger/`: Java class-level maintainability study; the adapter uses the
  expected readability Likert score (`4=easy` to `1=hard`) from its probability
  labels.
- `jetbrains/`: Java snippet readability study; the adapter joins source
  snippets with its binary human readability label, retaining vote counts and
  vote fraction as metadata.
- `code_jsonl/`: also loads the registered `generated_readability_90` ordinal
  generated-code dataset. Its source layout and canonical file are documented
  in `datasets/README.md`.
- `progressive_obfuscation/`: loads the grouped Java progressive-obfuscation
  benchmark. It validates the manifest, content hashes, and the complete L0--L6
  chain for every source class.

`code.py` exposes `load_code_dataset`, the dispatcher used by cross-method
code experiments and by CognaScore.

Add a dataset-specific adapter only when the shared JSONL schema is
insufficient. Every adapter returns `DatasetItem` instances; runners configure
experiments and delegate parsing here.
