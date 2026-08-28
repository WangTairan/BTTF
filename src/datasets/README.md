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
- `jetbrains/`: Java snippet readability study; the adapter uses the fraction
  of human votes marked readable as its continuous target. The released
  majority-vote binary label is retained as metadata for replication only.
- `code_jsonl/`: also loads the registered `generated_readability_90` ordinal
  generated-code dataset. Its source layout and canonical file are documented
  in `datasets/README.md`.
- `progressive_obfuscation/`: loads the grouped Java progressive-obfuscation
  trajectory dataset, validates its manifest and content hashes, and retains
  its cumulative L0--L6 ordinal target.
- `constructed_variants/`: strictly loads manifest-backed constructed Java
  datasets. Independent degradation/interference datasets retain pair identity
  and expected direction in metadata; they deliberately receive no artificial
  scalar severity ordering.

`code.py` exposes `load_code_dataset`, the dispatcher used by cross-method
code experiments and by CognaScore.

Add a dataset-specific adapter only when the shared JSONL schema is
insufficient. Every adapter returns `DatasetItem` instances; runners configure
experiments and delegate parsing here.
