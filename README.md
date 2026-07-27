# Code Readability Method Suite

This repository is a shared experiment workspace for code and natural-language
readability methods. It keeps datasets, method implementations, runners, result
outputs, and the GitHub Pages visualization in separate directories so new
methods and datasets can be added without changing unrelated experiments.

Current method families:

- CognaScore: the active code-readability feature and supervised Ridge pipeline.
  It extracts cognitive chunks, caches local embeddings, builds stable
  chunk-view clustering feature tables, and materializes the current visualized
  score.
- RMC: Recursive Masking Complexity. It masks control regions, asks the LLM to
  return exact mask replacements, and scores hidden regions directly.
- Posnett: deterministic Java readability model.
- Scalabrino: deterministic Java readability model using the released tool.
- CognaScore: Java lexeme embedding and clustering method.
- LLM: direct LLM readability scoring baseline.

Method-specific details live in each package README, especially
`src/methods/cognascore/README.md`, `src/methods/rmc/README.md`,
`src/methods/posnett/README.md`, and `src/methods/scalabrino/README.md`.

## Layout

```text
datasets/              Original and derived datasets
docs/                  Static visualization site for GitHub Pages
examples/              Small local examples
mask_playground/       Interactive single-mask recovery lab
models/                Local model/cache files
output/                Experiment outputs
src/datasets/          Dataset adapters
src/experiments/       Shared evaluation, paths, registry, statistics
src/methods/           Method implementations and method-specific runners
src/services/          LLM provider abstraction
src/site/              Static site generator
```

Dataset adapters return common `DatasetItem` objects. Method implementations
stay under `src/methods/<method>/`. Shared dataset/method registration is in
`src/experiments/registry.py`; path construction is in
`src/experiments/paths.py`.

## Datasets

Registered datasets:

| Key | Path | Type | Main metric |
| --- | --- | --- | --- |
| `mbjp` | `datasets/mbjp_dev_dataset/readability_dataset.json` | code, continuous | Spearman |
| `buse` | `datasets/buse` | code, continuous | Spearman |
| `scalabrino` | `datasets/scalabrino/dataset` | code, continuous | Spearman |
| `jetbrains` | `datasets/jetbrains` | code, binary | best-threshold MCC |
| `schnappinger` | `datasets/schnappinger` | code, continuous | Spearman |
| `dorn` | `datasets/dorn/dataset` | code, continuous | Spearman |
| `clear` | `datasets/CLEAR-Corpus-main/CLEAR_corpus_final.xlsx` | natural language, continuous | Spearman |
| `clear_dev` | `datasets/clear_dev_dataset/readability_dataset.xlsx` | natural language, continuous | Spearman |

Dorn is the original three-language dataset (`cuda`, `java`, `python`). The RMC
Dorn runner currently uses a token/fragment control matcher instead of Java AST
parsing so all three languages can be included.

## Outputs

Outputs are organized by method and dataset:

```text
output/<method>/<dataset>/...
```

Deterministic methods such as Posnett and Scalabrino write stable summaries and
overwrite reruns:

```text
output/posnett/<dataset>/summary.json
output/scalabrino/<dataset>/summary.json
```

Model-dependent methods keep the model layer:

```text
output/cognascore/<dataset>/<embedding-model>/summary.json
output/rmc/<dataset>/<llm-model>/summary.json
```

RMC result folders contain run-level and per-task configuration data so masking
and model parameters remain recoverable.

## Standard Method Evaluation

Use the shared evaluator for deterministic and direct scoring methods:

```bash
python3 -m src.experiments.evaluate_method \
  datasets/mbjp_dev_dataset/readability_dataset.json \
  --method posnett
```

Examples:

```bash
python3 -m src.experiments.evaluate_method datasets/mbjp_dev_dataset/readability_dataset.json --method posnett
python3 -m src.experiments.evaluate_method datasets/scalabrino/dataset --method scalabrino
python3 -m src.experiments.evaluate_method datasets/jetbrains --method cognascore
```

Continuous datasets report Spearman correlation. Binary datasets such as
JetBrains report MCC with the best threshold on that dataset.

CognaScore supports Dorn through the language-neutral lexical fallback in its
chunk extractor. Continuous datasets report Spearman; JetBrains reports MCC.

## CognaScore Feature Pipeline

CognaScore uses two persistent stages for embedding-derived features:

```text
output/cognascore_embeddings/<embedding-model>/embeddings.sqlite
output/cognascore_embedding_features/<dataset>/<embedding-model>/features.csv
```

The embedding cache is incremental: rerunning embeds only missing lexemes. When
the extractor changes, use `--replace-sources` for the selected datasets so
stale source references are removed before refreshed references are inserted.
Feature-table generation supports checkpoint/resume for long clustering runs.

Repair the current Nomic cache and feature table after extractor changes:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache python3 -m src.methods.cognascore.runners.embeddings \
  datasets/schnappinger \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --device cpu \
  --batch-size 8 \
  --quiet \
  --replace-sources
```

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache python3 -m src.methods.cognascore.runners.embedding_features \
  datasets/schnappinger \
  --embedding-model nomic-ai/nomic-embed-text-v1.5 \
  --max-vectors-per-task 512 \
  --resume \
  --update-all \
  --checkpoint-every 1
```

Run the supervised Ridge materialization after base and embedding feature
tables are current:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache python3 -m src.methods.cognascore.runners.supervised_ridge
```

## RMC Experiments

RMC masks code or text, asks a recovery model to fill the masks, and compares
the recovered result with the original using sequence similarity. Current code
experiments use:

```text
model: gpt41-nano
similarity: sequence
granularity: control
ast_min_tokens: 3
max_combination_size: 1
max_samples_per_stratum: unlimited unless explicitly provided
```

Code prompts are language-neutral. They no longer mention Java, so the same
prompt can be used for Java, CUDA, and Python fragments.

Run current masked RMC code datasets from small to large:

```bash
python3 -m src.methods.rmc.runners.mbjp \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 3 \
  --max-combination-size 1
```

```bash
python3 -m src.methods.rmc.runners.dorn \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 3 \
  --max-combination-size 1
```

```bash
python3 -m src.methods.rmc.runners.jetbrains \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 3 \
  --max-combination-size 1
```

```bash
python3 -m src.methods.rmc.runners.scalabrino \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 3 \
  --max-combination-size 1
```

Expected recovery counts for the current control configuration:

```text
MBJP         69
Dorn       1149
JetBrains   651
Scalabrino  733
```

Use `--skip-existing` to resume after interruption without rewriting completed
`result.json` files. Omit it when intentionally rerunning after a prompt or
configuration change.

Useful RMC controls:

- `--limit N`: run the first `N` selected items.
- `--start N`: start after filtering at index `N`.
- `--task-id ID`: run a specific task; can be repeated.
- `--skip-existing`: reuse existing completed task outputs.
- `--mock-recover`: run deterministic local recovery for smoke tests.
- `--max-samples-per-stratum N`: sample at most `N` combinations per stratum;
  if omitted, all non-overlapping combinations up to `--max-combination-size`
  are used.

## Visualization Site

The static site is generated into `docs/`:

```bash
python3 -m src.site.build
```

The homepage is a method-by-dataset result matrix. Dataset and run pages list
samples with sortable columns such as human label/score, method scores, and
LOC. Sample pages use one shared view for all entry points and show the source
code plus method-specific evidence, such as Posnett tokens, RMC hard control
regions, CognaScore cluster summaries, and LLM scores with reasoning.

## Mask Recovery Lab

The local Lab supports interactive single-region experiments across the code
datasets. Select source code on the left, inspect or edit the system-prompt and
few-shot sections, choose a model, and run one recovery. The mask task is
generated from the current selection and is not stored in the three per-template
custom prompt caches.

```bash
python3 -m mask_playground.server
```

Open `http://127.0.0.1:8765`. The result panel reports exact match, sequence,
token Jaccard, token cosine, and BLEU. Edit distance and other quadratic
dynamic-programming metrics are intentionally excluded from this interface.

## LLM Keys

Set the provider key required by the selected model alias in
`src/services/llm.py`:

```bash
export OPENAI_API_KEY=...
export GROQ_API_KEY=...
export OPENROUTER_API_KEY=...
export DEEPSEEK_API_KEY=...
```

Clients and keys are loaded lazily. The repository and Lab can start with only
some keys configured; a missing key is reported immediately only when a model
from that provider is run.

For supported providers, dataset RMC runs use batch recovery and store
`.batch_state.json` so interrupted submitted batches can resume polling instead
of submitting duplicate requests.

## Development Notes

- Add datasets under `src/datasets/<dataset>/` and register them in
  `src/experiments/registry.py`.
- Add methods under `src/methods/<method>/`; method-specific runners belong in
  the method package.
- Keep generated results under `output/`; keep visualization output under
  `docs/`.
- Prefer smoke tests with `--mock-recover --limit 1` before long LLM runs.
