# Dataset Adapters

Dataset-specific parsing lives here, separately from metric execution:

- `clear/`: CLEAR spreadsheet passages.
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

`code.py` exposes `load_code_dataset`, the dispatcher used by cross-method
code experiments and by CognaScore.

Add a new dataset as `src/datasets/<dataset>/` and expose a `load_dataset`
function that returns `DatasetItem` instances. Runner modules should configure
the experiment and delegate parsing to these adapters.
