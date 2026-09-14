# Independent Source Interferences

This package constructs Java and Python readability-interference datasets and
provides optional downstream behavior-prediction and code-repair experiments.
It is maintained alongside CognaScore, but does not import its feature extractor
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
| Formal Java/Python datasets used by CognaScore | `datasets/constructed/` |
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

This runs the CognaScore, integration, and tool tests without rebuilding study
datasets or calling APIs. Detailed downstream commands and validation limits
are documented in [the guide](docs/guide.md). Provider runners require the
appropriate credentials and explicit task inputs; these optional experiments
do not run during installation or release checks.

For tool development, install `tools/source_interference[dev]`. Its Ruff
configuration checks unused/undefined names and import order; formatting uses
an 88-column line width. Run `ruff check tools/source_interference` and
`ruff format --check tools/source_interference` before submitting tool changes.
