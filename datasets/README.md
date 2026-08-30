# Datasets

Dataset parsing is implemented under `src/datasets/`; canonical paths and
evaluation metrics are registered in `src/experiments/registry.py`.

| Registry key | Canonical path | Label | Primary metric |
| --- | --- | --- | --- |
| `mbjp` | `mbjp_dev_dataset/readability_dataset.json` | continuous | Spearman |
| `buse` | `buse/` | continuous | Spearman |
| `scalabrino` | `scalabrino/dataset/` | continuous | Spearman |
| `jetbrains` | `jetbrains/` | continuous vote fraction | Spearman |
| `dorn` | `dorn/dataset/` | continuous | Spearman |
| `schnappinger` | `schnappinger/` | continuous | Spearman |
| `java_comparative_obfuscation` | `constructed/java-comparative-obfuscation-class-100/` | paired direction | paired response rate |
| `python_comparative_degradation` | `constructed/python-comparative-degradation-class-100/` | paired direction | paired response rate |

## Independent interference datasets

The Java and Python constructed datasets each contain 100 original production
classes and 14 interference types applied independently to every original.
Their 1,500 rows comprise 100 originals and 1,400 attempted transformations.
Manifest order is an identifier, not a scalar severity label. Evaluation
compares every source-changing transformation directly with its matched
original and excludes inapplicable, unchanged pairs from changed-only rates.

The interferences cover comments, identifiers, expressions, code injection,
layout, data flow, and control flow. The Java sources are balanced across
Apache Kafka, Google Guava, Netty, and Spring Framework; the Python sources are
balanced across Django, Flask, Requests, and attrs. Every manifest records
content hashes and construction provenance for incremental recomputation.
