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
- `code_jsonl/`: also loads the two registered generated-code datasets:
  `generated_readability_90` (ordinal) and
  `generated_binary_readability` (binary). Their source layout and canonical
  files are documented in `datasets/README.md`.

`code.py` exposes `load_code_dataset`, the dispatcher used by cross-method
code experiments and by CognaScore.

Add a dataset-specific adapter only when the shared JSONL schema is
insufficient. Every adapter returns `DatasetItem` instances; runners configure
experiments and delegate parsing here.
