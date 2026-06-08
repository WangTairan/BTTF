# Code Readability Method Suite

This repository is a shared experiment workspace for code and natural-language
readability methods. It keeps datasets, method implementations, runners, result
outputs, and the GitHub Pages visualization in separate directories so new
methods and datasets can be added without changing unrelated experiments.

Current method families:

- RMC: Recursive Masking Complexity, including masked code RMC, prefix RMC, and
  natural-language RMC variants.
- Posnett: deterministic Java readability model.
- Scalabrino: deterministic Java readability model using the released tool.
- CognaScore: Java lexeme embedding and clustering method.
- LLM: direct LLM readability scoring baseline.

Method-specific details live in each package README, especially
`src/methods/rmc/README.md`, `src/methods/posnett/README.md`,
`src/methods/scalabrino/README.md`, and `src/methods/cognascore/README.md`.

## Layout

```text
datasets/              Original and derived datasets
docs/                  Static visualization site for GitHub Pages
examples/              Small local examples
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
output/rmc_masked/<dataset>/<llm-model>/summary.json
output/rmc_prefix/<dataset>/<llm-model>/summary.json
output/rmc_natural_language/<dataset>/<llm-model>/summary.json
```

RMC result folders also contain a `config.json` at the run level and per-task
`config.json` files so masking and model parameters remain recoverable.

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

CognaScore intentionally excludes Dorn in the shared evaluator because its
current extractor is Java-oriented and Dorn contains truncated fragments across
three languages.

## RMC Experiments

RMC masks code or text, asks a recovery model to fill the masks, and compares
the recovered result with the original using sequence similarity. Current code
experiments use:

```text
model: gpt41-nano
similarity: sequence
granularity: control
ast_min_tokens: 8
max_combination_size: 3
max_samples_per_stratum: unlimited unless explicitly provided
```

Code prompts are language-neutral. They no longer mention Java, so the same
prompt can be used for Java, CUDA, and Python fragments.

Run current masked RMC code datasets from small to large:

```bash
python3 -m src.methods.rmc.runners.mbjp \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 8 \
  --max-combination-size 3
```

```bash
python3 -m src.methods.rmc.runners.dorn \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 8 \
  --max-combination-size 3
```

```bash
python3 -m src.methods.rmc.runners.jetbrains \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 8 \
  --max-combination-size 3
```

```bash
python3 -m src.methods.rmc.runners.scalabrino \
  --model gpt41-nano \
  --ast-granularity control \
  --ast-min-tokens 8 \
  --max-combination-size 3
```

Expected recovery counts for the current control configuration:

```text
MBJP        158
Dorn       2115
JetBrains  2393
Scalabrino 3386
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

Compute RMC correlations from a completed result folder:

```bash
python3 -m src.methods.rmc.runners.spearman \
  output/rmc_masked/<dataset>/<model>
```

## Natural-Language RMC

CLEAR uses natural-language masking rather than code masking:

```bash
python3 -m src.methods.rmc.runners.clear \
  --dataset datasets/clear_dev_dataset/readability_dataset.xlsx \
  --model gpt41-nano
```

Natural-language masks operate at sentence or paragraph granularity depending on
the runner arguments. The prompt asks for passage completion rather than code
completion.

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

## LLM Keys

Set the provider key required by the selected model alias in
`src/services/llm.py`:

```bash
export OPENAI_API_KEY=...
export GROQ_API_KEY=...
export OPENROUTER_API_KEY=...
```

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
