# Datasets

Dataset parsing is implemented under `src/datasets/`; canonical paths and
evaluation metrics are registered in `src/experiments/registry.py`.

| Registry key | Canonical path | Label | Primary metric |
| --- | --- | --- | --- |
| `mbjp` | `mbjp_dev_dataset/readability_dataset.json` | continuous | Spearman |
| `buse` | `buse/` | continuous | Spearman |
| `scalabrino` | `scalabrino/dataset/` | continuous | Spearman |
| `jetbrains` | `jetbrains/` | binary | MCC |
| `dorn` | `dorn/dataset/` | continuous | Spearman |
| `schnappinger` | `schnappinger/` | continuous | Spearman |
| `generated_readability_90` | `readability_dataset_90.jsonl` | ordinal | Spearman |
| `generated_binary_readability` | `readability_binary.jsonl` | binary | MCC |

## Generated Readability 90

`readability_dataset_90.jsonl` contains 90 Java examples generated under three
readability instructions: `low`, `normal`, and `high`. Each row preserves the
source dataset identifier, source item identifier, generator model, language,
instruction label, and code. The adapter maps the ordered labels to `0.0`,
`0.5`, and `1.0` for rank-based evaluation.

## Generated Binary Readability

`high/` and `low/` contain the source Java files for the binary dataset.
`readability_binary.jsonl` is its canonical combined representation and
contains 100 high- and 100 low-readability examples. Rebuild it deterministically
with:

```bash
python scripts/build_binary_readability_dataset.py
```

The loader maps `low` to `0.0` and `high` to `1.0`. The registered primary
metric is Matthews correlation coefficient (MCC).

Both generated datasets are retained as formal additional evaluation datasets.
They are distinct from the six established datasets used in the current
feature-selection study.
