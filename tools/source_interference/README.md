# Independent Source Interferences

This package constructs Java and Python readability-interference datasets and
provides optional downstream behavior-prediction and code-repair experiments.
It is maintained alongside the primary readability model, but does not import its feature extractor
or fit its readability predictor.

## Organization

```text
src/readability_data/
  java_degradation/      Tree-sitter Java engine, plugins, and construction
  python_degradation/    Python AST validation, sampling, and construction
  shared/                Language-aligned interference contract and resources
src/readability_experiments/
  common/                Task catalogs, storage, paths, and shared contracts
  benchmark_eval/        Defects4J/BugsInPy task and validation tooling
  lightweight_eval/      Lightweight executable repair tasks
  providers/             Provider-specific API support
tests/                   Generation and downstream-runner regression tests
docs/guide.md            Detailed protocols and command reference
notes/                   Local research drafts
```

The language implementations are separate; the shared contract defines 13
independent interferences in seven categories: comments, identifiers,
expressions, code injection, layout, data flow, and control flow. Each
interference is applied directly to the same original, never cumulatively.
Each 100-class dataset contains 100 originals and 1,300 attempted variants.
Inapplicable operations retain unchanged source and remain identifiable in the
manifest; response-rate evaluation excludes unchanged pairs.

Java uses Tree-sitter Java validation and Python uses `ast.parse`. Construction
is staged and publishes each dataset only after validation succeeds. Existing
output directories are refused. These checks establish syntactic validity, not
project-level compilation or strict semantic equivalence.

## Installation and reproduction

All examples run from the repository root. The root `requirements.txt` installs
this package in editable mode. To install only the generator and its tests:

```bash
python -m pip install -e 'tools/source_interference[test]'
python -m readability_data.cli list-java-interferences
python -m readability_data.cli list-python-interferences
```

The Java input corpus must contain complete `.java` classes. For the retained
study, the prepared corpus is
`artifacts/source_interference/data/base/java-readable-class-100/source-original/`.
Python construction requires local Django, Flask, Requests, and attrs checkouts
under `artifacts/source_interference/data/raw/`. Use the commits recorded in
the formal datasets' `provenance.json`; upstream contents affect sampling and
generated variants. These source caches are local prerequisites, not bundled
or automatically downloaded by the generation command.

Generate separate reproduction copies sequentially:

```bash
bash scripts/generate_constructed_datasets.sh
```

The default output is `artifacts/source_interference/reproductions/`.
`OUTPUT_ROOT`, `WORKSPACE`, `JAVA_INPUT`, `RAW_ROOT`, `PYTHON_BIN`, and `SEED`
can be supplied explicitly. No embedding, model fitting, scoring, or API call
runs as part of this command.

## Storage boundaries

| Content | Repository-relative location |
| --- | --- |
| Formal Java/Python datasets used by the primary model | `datasets/constructed/` |
| Upstream checkouts and prepared source corpus | `artifacts/source_interference/data/raw/`, `data/base/` inside that workspace |
| Downstream tasks, benchmarks, and validation workspaces | `artifacts/source_interference/data/` |
| API run records, responses, and usage | `results/experiments/source_interference/` |

There is no tool-local copy of the formal datasets. Downstream CLI defaults are
resolved from the repository location rather than the caller's current
directory. Relative workspace options resolve inside
`artifacts/source_interference/`; explicit absolute paths are supported. For a
non-editable installation, set `READABILITY_REPOSITORY_ROOT` to the repository
root. Local raw checkouts, caches, API records, and credentials are ignored by
the root `.gitignore`; they are not submodules.

## Tests and optional downstream experiments

```bash
bash scripts/check_release.sh
```

This runs the primary-model, integration, and tool tests without rebuilding study
datasets or calling APIs. Detailed downstream commands and validation limits
are documented in [the guide](docs/guide.md). Provider runners require the
appropriate credentials and explicit task inputs; these optional experiments
do not run during installation or release checks.

The recent-repository completion pilot uses one pinned September 2026
production change from Apache Commons Collections and one from pytest. It
replaces the recently changed method body with the same hole before applying
each interference, then retains a pair only when the repository's focused
native tests pass with the gold completion and fail with the hole. Repository
checkouts and build caches remain under `artifacts/source_interference/`:

```bash
bash scripts/build_recent_completion_pilot.sh
```

The pilot builder performs no model request. It writes the validated task
manifest, native-test evidence, and report under
`artifacts/source_interference/data/experiments/recent-repository-completion/`.

For the expanded study, discover 25 recent Java functions and 25 recent
Python functions before running native validation. Each manifest row records
both a method-body span and a recently changed statement span, together with
the pinned repository commit, source hash, completion hashes, origin commits,
and focused test paths:

```bash
bash scripts/discover_recent_completion_targets.sh
```

This command only builds the immutable candidate manifest. It does not modify
either checkout, run repository tests, construct interference variants, or
call a language model.

Validate the candidates incrementally with the repositories' focused native
tests:

```bash
bash scripts/validate_recent_completion_holes.sh
```

For each target, the unchanged source must pass, both validation-hole variants
must remain syntactically valid, and a hole is retained only when its focused
tests fail. `PER_LANGUAGE=1` performs a two-repository smoke test; the default
checks the complete manifest. Results and logs are checkpointed under
`native-validation/`, so restarting does not repeat completed targets.
The retained `balanced_targets.jsonl` contains the newest 25 qualified targets
per language; all passing candidates remain available in
`qualified_targets.jsonl` for later expansion.

Run a small Python-only solvability screen with the official DeepSeek API:

```bash
LIMIT_TARGETS=5 bash scripts/run_recent_completion_python_pilot.sh
```

The model receives the pinned source file with one
`<READABILITY_HOLE>` but receives neither the original completion nor the
tests. Method-body and statement completions are scored separately by
reinserting the response and running the hidden focused pytest command. The
default pilot deliberately uses the shortest five validated Python targets;
it is a pipeline and solvability check, not an estimate of full-corpus
accuracy. Full provider responses, reasoning, token usage, normalized
completions, and native-test logs are saved under `results/experiments/`.

The original-versus-interference experiment requires a second native
validation stage; the 48 original Python holes alone are not the final task
count. Build the paired manifest before making API requests:

```bash
bash scripts/build_recent_completion_python_variants.sh
```

Each of the 13 independently applied interferences is retained for a hole only
when it changes the model-visible context, the transformed source passes after
restoring its transformed completion, and the corresponding transformed hole
fails the same focused test command. Inapplicable, hidden-only, duplicate, and
test-breaking variants do not become model tasks. The resulting `tasks.jsonl`
contains the original condition and every natively qualified perturbation.

The completed Python task input is also committed as a pinned local dataset:
[`datasets/recent_repository_completion/pytest_python/`](../../datasets/recent_repository_completion/pytest_python/).
It contains the pytest source snapshot, 507 task records, provenance and
checksums. Ordinary model evaluation uses this archive rather than repeating
discovery or fetching the upstream repository. Restore it offline with
`python scripts/local_recent_completion_dataset.py restore`.

For tool development, install `tools/source_interference[dev]`. Its Ruff
configuration checks unused/undefined names and import order; formatting uses
an 88-column line width. Run `ruff check tools/source_interference` and
`ruff format --check tools/source_interference` before submitting tool changes.
