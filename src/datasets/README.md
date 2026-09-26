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
- `constructed_variants/`: strictly loads manifest-backed constructed Java
  and Python independent-interference datasets. Pair identity and expected
  direction are retained in metadata; variants deliberately receive no
  artificial scalar severity ordering. Java manifests identify pairs with
  `group_id`; Python manifests use `base_sample_id`, which the adapter exposes
  through the same normalized `group_id` metadata field.

`code.py` exposes `load_code_dataset`, the dispatcher used by cross-method
code experiments and by the primary readability model.

Add a dataset-specific adapter only when the shared JSONL schema is
insufficient. Every adapter returns `DatasetItem` instances; runners configure
experiments and delegate parsing here.
