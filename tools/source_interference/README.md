# Independent Source Interferences

This package constructs the Java and Python readability-interference datasets
used to evaluate the frozen readability model. It does not import the feature
extractor or fit the readability predictor.

## Organization

```text
src/readability_data/
  java_degradation/      Tree-sitter Java engine, plugins, and construction
  python_degradation/    Python AST validation, sampling, and construction
  shared/                Language-aligned interference contract and resources
tests/                   Generator regression tests
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

There is no tool-local copy of the formal datasets. Local raw checkouts and
generated reproduction copies are ignored by the root `.gitignore`; they are
not submodules.

## Tests

```bash
bash scripts/check_release.sh
```

This runs the primary-model, integration, and source-generation tests without
rebuilding study datasets.

For tool development, install `tools/source_interference[dev]`. Its Ruff
configuration checks unused/undefined names and import order; formatting uses
an 88-column line width. Run `ruff check tools/source_interference` and
`ruff format --check tools/source_interference` before submitting tool changes.
