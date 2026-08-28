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
| `generated_readability_90` | `generated_readability_90/dataset.jsonl` | ordinal | Spearman |
| `java_progressive_obfuscation` | `constructed/java-progressive-obfuscation-class-100/` | grouped ordinal | Spearman + within-chain trend |
| `java_comparative_obfuscation` | `constructed/java-comparative-obfuscation-class-100/` | paired direction | paired response rate |

## Generated Readability 90

`generated_readability_90/dataset.jsonl` contains 90 Java examples generated under three
readability instructions: `low`, `normal`, and `high`. Each row preserves the
source dataset identifier, source item identifier, generator model, language,
instruction label, and code. The adapter maps the ordered labels to `0.0`,
`0.5`, and `1.0` for rank-based evaluation.

This generated dataset is retained as a formal additional evaluation dataset.
It is distinct from the six established datasets used in the current
feature-selection study.

## Java Progressive Obfuscation

`constructed/java-progressive-obfuscation-class-100/` contains 100 complete
Java classes, each represented by an original version (L0) and six cumulative
obfuscation stages (L1--L6). The adapter maps a stage to the ordinal target
`1 - level / 6`; this target records construction order rather than an
independent human readability judgment. Evaluation reports both pooled
Spearman and within-class chain-direction measurements. Transitions that leave
a particular class unchanged are identified separately.

## Comparative Obfuscation

`constructed/java-comparative-obfuscation-class-100/` contains 12 interference
types independently applied to 100 original Java classes. Because the
transformations are independent, manifest order is not treated as a scalar
severity label; evaluation compares every transformed class directly with its
matched original.
