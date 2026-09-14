# Source-interference tool: detailed guide

This guide covers source generation and optional downstream experiments, not
CognaScore feature selection. Dataset generation refuses existing output paths;
use a separate output directory for reproduction. Source checkouts and local
workspaces are not included in Git. See `tools/source_interference/README.md`
for storage boundaries and prerequisites.

This project constructs less-readable variants of complete Java and Python source
classes. Java degradation processes a prepared class corpus. The aligned Python
experiment deterministically selects a balanced corpus from four pinned upstream
projects. In both languages, comparative interferences act independently on the same
original source class.

The implementation is organized by language at the same architectural level:

```text
readability_data/
├── java_degradation/       # Java engine, registry, plugins, and pipeline
├── python_degradation/     # Python sampling, plugins, and pipeline
├── shared/                 # contracts, HTML explorer, and shared resources
└── cli.py                  # language-explicit command entry points
```

`java_degradation` and `python_degradation` do not import one another. Shared plugin
contracts and presentation code live above both language implementations.

## Cross-language alignment

The comparative Java and Python experiments follow the machine-readable contract in
`shared/alignment.py`. Alignment means that both languages use the same:

- ordered set of 13 interferences and seven categories;
- direct-from-original application protocol;
- target cardinality (`all`, every callable, or one callable per class);
- ten-template families for readable or opaque injected code;
- deterministic template selection, target ranking, and collision handling;
- aligned hexadecimal-notation and numeric-intermediate policies;
- fixed layout dose (40% of eligible groups while retaining at least two);
- statistics vocabulary for the principal operation counts.

The implementations differ only where the language grammar requires it. Python
documentation is represented by docstrings rather than Javadoc; Python layout changes
retain significant indentation; condition inversion excludes syntax forms that cannot
be safely reconstructed source-locally; and injected snippets use each language's
normal control-flow and naming conventions.

## Installation

All commands in this guide run from the monorepo root after installing its
`requirements.txt`. For the generator alone, install:

```bash
python -m pip install -e 'tools/source_interference[test]'
```

Default downstream paths are resolved from the repository, not the current
working directory. Explicit absolute paths override these defaults. Relative
workspace options such as `--output` are resolved inside
`artifacts/source_interference/`.

## Constructed datasets

The toolkit retains one independent-interference experiment per language:

```text
comparative: source -> interference 1
             source -> interference 2
             ...
             source -> interference 13
```

Every pluggable interference is measured directly against the same readable source,
avoiding interactions between different operations.

The current directories are:

```text
datasets/constructed/
├── java-comparative-obfuscation-class-100/
└── python-comparative-degradation-class-100/
```

## Aligned Python experiment

The Python module mirrors the Java comparative design with Django, Flask, Requests,
and attrs. It selects 25 complete top-level production classes per project, prioritizes
classes containing methods, and excludes tests, documentation, examples, and Django
migrations. The fixed seed and exact repository commits are written to
`provenance.json`.

Each of the 13 plugins is applied directly to the original class. The result therefore
contains 100 originals and 1,300 independently degraded variants (1,400 `.py` files):

```bash
readability-data python-construct \
  --django-root artifacts/source_interference/data/raw/django \
  --flask-root artifacts/source_interference/data/raw/flask \
  --requests-root artifacts/source_interference/data/raw/requests \
  --attrs-root artifacts/source_interference/data/raw/attrs \
  --output artifacts/source_interference/reproductions/python-comparative-degradation-class-100 \
  --per-project 25 \
  --seed 20260823
```

Python plugins use the same seven categories and slugs as Java: one comment operation,
three identifier operations, two expression operations, two data-flow operations,
three code-injection operations, one layout operation, and one control-flow operation.
Identifier and data-flow edits are function-scope aware.
Because indentation is grammatical in Python, layout degradation only removes selected
blank lines and line breaks inside bracketed expressions. Every extracted source and
generated variant must pass UTF-8 decoding and `ast.parse`.

The Python implementation is isolated under `python_degradation/`; its category
folders implement the same pluggable `category`, `slug`, `description`, and `apply`
contract as the Java module.

## Build one dataset per interference

Generate every catalogued interference directly and separately from the same source:

```bash
readability-data java-interfere \
  --input artifacts/source_interference/data/base/java-readable-class-100/source-original \
  --output artifacts/source_interference/reproductions/java-comparative-obfuscation-class-100 \
  --seed 20260823
```

No interference consumes another interference's output. The result contains one source
version and one version for each of the 13 plugins per class. Directories are grouped by
category and plugin:

```text
output/
├── source-original/
├── comments/remove-comments/
├── identifiers/shorten-identifiers/
├── expressions/encode-integer-literals/
├── data-flow/introduce-numeric-intermediates/
├── data-flow/inline-intermediate-variables/
├── control-flow/lower-for-to-while/
├── code-injection/inject-readable-unrelated-code/
├── layout/partially-compact-layout/
├── manifest.jsonl
├── provenance.json
└── obfuscation-report.html
```

Use `--interferences` followed by plugin slugs to generate only a subset.

## Pluggable interference interface

Every interference implements the generic `Interference` contract from
`shared/contracts.py`. Java uses `bytes`; Python uses `str`:

```python
class Interference(ABC, Generic[SourceT]):
    category: str
    slug: str
    description: str

    @abstractmethod
    def apply(
        self, source: SourceT, context: InterferenceContext
    ) -> TransformResult[SourceT]: ...
```

Operations are grouped by mechanism rather than degradation level:

```text
interferences/
├── comments/          # comment and documentation removal
├── identifiers/       # shortening, misleading names, and ProGuard-style short names
├── expressions/       # condition inversion and hexadecimal integer notation
├── data_flow/          # introduction and removal of intermediate variables
├── code_injection/    # dead branches, readable code, and opaque code
├── layout/            # partial visual compaction
├── control_flow/      # conservative lowering of ordinary for loops to while loops
└── core/              # plugin contract and Java syntax utilities
```

The full catalog currently contains 13 independently applied plugins in a single
machine-readable order shared by Java and Python.

The `garble-identifiers` plugin independently implements ProGuard's documented
short-name strategy: identifiers are assigned in stable order from `a` through `z`,
then `A` through `Z`, followed by `aa`, `ab`, and so on. The source-level adaptation
also skips Java keywords and existing names to preserve syntactic validity and avoid
collisions. It does not copy or depend on ProGuard code. The reference behavior was
verified against Guardsquare's
[`SimpleNameFactory`](https://github.com/Guardsquare/proguard/blob/be8170263eb363bd82bbab81b874b693c6f669a6/base/src/main/java/proguard/obfuscate/SimpleNameFactory.java).

The newly available plugins are:

| Category | Plugin | Reliability boundary |
|---|---|---|
| Identifiers | `mislead-identifiers` | Selects length-matched meaningful but unrelated names from compact controlled pools and resolves collisions |
| Expressions | `encode-integer-literals` | Rewrites every eligible decimal integer literal using lowercase hexadecimal notation while preserving Java long suffixes |
| Data flow | `introduce-numeric-intermediates` | Replaces each eligible in-function decimal integer with the sum of two fresh short-named locals inserted before its containing statement |
| Data flow | `inline-intermediate-variables` | Inlines every eligible single-use local variable by substituting its parenthesized initializer expression |
| Control flow | `lower-for-to-while` | Rewrites every safely eligible ordinary `for` loop as an explicit iterator or initializer/condition/update `while` loop |
| Code injection | `inject-readable-unrelated-code` | Selects one of ten structured templates at a deterministic callable location |
| Code injection | `inject-low-readability-unrelated-code` | Selects one of ten opaque templates at a deterministic callable location |

Both code-injection plugins use fresh identifiers, keep all state inside a nested local
block, and place constructor code after a required `super(...)` or `this(...)` call.
Template selection is pseudorandom but reproducible from the seed and class identity.
Readable templates use complete names such as `runningTotal` and `currentNumber`; a
numeric suffix is added only when the source class already uses the same name. Opaque
templates intentionally use compact formatting, bitwise expressions, hexadecimal
literals, and meaningless names. Both groups contain exactly ten templates and inject
at most one block per class, keeping their treatment amount comparable.

Integer encoding rewrites decimal notation uniformly as lowercase hexadecimal notation;
it does not alter Boolean literals or recursively process literals that are already
hexadecimal. The numeric-intermediate plugin applies only inside callable bodies. For
each eligible integer it introduces two fresh locals named from the shortest available
legal sequence (`a`, `b`, `c`, and so on) and replaces the literal with their sum. Java
uses `final int` or `final long` declarations so the introduced values remain constants;
Python inserts ordinary local assignments. Existing identifiers and language keywords
are skipped, and explicit Java constructor invocations are not modified.

Intermediate-variable inlining targets only independently declared locals with an
initializer, exactly one read, no later assignment or deletion, and a read in a later
simple statement of the same lexical block. Java multi-declarator statements and array
initializers are excluded; Python destructuring, semicolon-packed assignments,
f-string references, and repeated-execution scopes are excluded. The declaration is
removed and its sole reference is replaced by a parenthesized copy of the initializer.
Every variable satisfying these conservative eligibility rules is inlined; no additional
fractional sampling is applied.

Misleading identifier replacement uses separate controlled pools for local or parameter
names and method names. Fixed short base words are combined with a limited set of short
prefixes, verbs, and objects, producing 494 local-name candidates and 521 method-name
candidates. Candidates are ranked first by absolute length difference from the original
identifier and then reproducibly shuffled within each length-distance group using the
seed, sample, and declaration position. Exact-length unrelated names are therefore
preferred whenever available, while type and semantics are not considered. Names range
from 3--14 characters for locals and 3--15 for methods. Conflicting names are skipped,
and a letter-only fallback is available if a pool is exhausted; no numeric suffix is
generated. Per-run statistics record exact-length matches, total length difference,
pool selections, skipped collision candidates, and alphabetic fallback use.

`lower-for-to-while` is exhaustive over the forms that can be reconstructed reliably
from one source file. Java classic loops become a scoped initializer plus a `while`
body and trailing updates. Enhanced loops over arrays use an explicit index; loops over
`Iterable` values use an explicit `Iterator`. Source expressions are evaluated once and
fresh helper names avoid collisions. Labeled loops, header comments, unknown enhanced
source types, and classic loops whose update semantics would be changed by `continue`
are retained. Python synchronous loops use an explicit iterator, `next`, and
`StopIteration`; `for...else`, asynchronous loops, single-line suites, and
comment-bearing loop regions are retained. Every skip reason and successful lowering is
counted in each sample's transformation statistics.

List the complete catalogs:

```bash
readability-data list-java-interferences
readability-data list-python-interferences
```

The shorter commands `interfere` and `list-interferences` remain aliases for their
Java counterparts.

To add an operation:

1. implement `Interference` in a new module;
2. return transformed bytes plus integer statistics;
3. register the instance in the language registry;
4. add focused syntax, determinism, and behavior-boundary tests.

Both language pipelines automatically use the aligned registry.

## Executable repair benchmarks

The downstream agent experiment is isolated from the constructed readability
corpora under `readability_experiments/benchmark_eval`. It uses Defects4J for Java
and BugsInPy for Python. The benchmark frameworks and their complete metadata live
under `artifacts/source_interference/data/benchmarks/frameworks`; per-bug repositories are checked out on demand
instead of being duplicated for every instance.

Build the complete lightweight catalogs:

```bash
python -m readability_experiments.benchmark_eval.cli
```

The generated files are:

```text
artifacts/source_interference/data/benchmarks/catalogs/repair-benchmarks/
├── defects4j.jsonl
├── bugsinpy.jsonl
└── report.json
```

Each record contains the benchmark and project identifiers, buggy and fixed
revisions, test metadata, developer-patch paths and hash, and the set of modified
production source files. The current catalogs contain 854 active Defects4J bugs and
501 metadata entries in the current BugsInPy repository snapshot.

An end-to-end validation pilot uses Defects4J Lang-1 (`NumberUtils`) and BugsInPy
PySnooper-2 (`Tracer`). For each instance, all 13 interferences are independently
applied to the same complete class in both the buggy and fixed revisions. A variant
is retained only when the buggy revision still fails with the expected marker and
the fixed revision still passes:

```bash
python -m readability_experiments.benchmark_eval.pilot
```

The pilot requires prepared benchmark worktrees, Maven, JDK 11, and the
historical BugsInPy environment. It discovers Maven on `PATH` and JDK 11 through
the configured Java environment; `--maven`, `--java-home`, and `--python-bin`
provide explicit overrides. Missing prerequisites are reported as errors, not
replaced by synthetic evaluation results.

Results, transformed class sources, and complete test logs are written under
`artifacts/source_interference/data/experiments/agent-readability/validation-pilot`. The pilot leaves both source
worktrees restored to their original source hashes after every transformation.

To measure class-level applicability without compiling projects, running tests, or
calling an LLM, run the static validator with its fixed default seed (`20260823`):

```bash
python -m readability_experiments.benchmark_eval.static_cli
```

It obtains each buggy/fixed source pair, selects the changed top-level class, and
applies all 13 language-aligned interferences independently. A condition is usable
only when both revisions change and both transformed complete source files parse.
The task-level exclusions, per-interference applicability, parse failures, hashes,
and aggregate counts are written to
`artifacts/source_interference/data/experiments/agent-readability/static-validation`.

An explicit Java plugin or ordered plugin sequence can also be exercised directly:

```python
from readability_data.java_degradation import JavaInterferenceEngine

result = JavaInterferenceEngine(seed=20260823).apply_interferences(
    source,
    identity="example",
    slugs=["inject-readable-unrelated-code", "mislead-identifiers"],
)
```

## Output

Each complete run writes:

```text
output/
├── source-original/
├── <category>/<interference>/
├── manifest.jsonl
├── provenance.json
└── obfuscation-report.html
```

The manifest records source identity, the applied interference, transformation
statistics, line count, and content hashes. Every transformed version points directly
to its original source version. Provenance records the implementation and target policy
used by each plugin.

## LLM task experiment candidates

Behavior prediction and test-guided repair live in the separate
`readability_experiments` package. The builders treat the raw and base source
caches under `artifacts/source_interference/data/` and the formal datasets under
`datasets/constructed/` as immutable inputs and write only beneath
`artifacts/source_interference/data/experiments`.

```bash
python -m readability_experiments.cli \
  --workspace "$PWD/artifacts/source_interference" \
  --output "$PWD/artifacts/source_interference/data/experiments"
```

The command creates two independent inventories:

```text
artifacts/source_interference/data/experiments/
├── behavior-prediction/
│   ├── candidates.jsonl
│   └── report.json
└── test-guided-repair/
    ├── candidates.jsonl
    └── report.json
```

Records link to existing original and transformed class variants by path and
SHA-256 hash. Repair candidates also contain deterministic AST mutation
anchors. A `static_candidate` is not claimed to be executable: it must still
pass the restoration, build, clean-test, mutant-test, and paired-oracle checks
listed in `required_validation`.

The fixed repair manifests use the single-message `single-message-repair-v2`
template. Each prompt contains the complete target source file, the relevant
released test method or class, and—when the benchmark releases it—the observed
failure. Benchmark names, bug IDs, interference labels, fixed sources, and
developer patches are excluded from the prompt. Test evidence is fixed once per
base bug and reused byte-for-byte across all 14 source conditions.

```bash
python -m readability_experiments.benchmark_eval.sample_cli \
  --workspace "$PWD/artifacts/source_interference" \
  --output "$PWD/artifacts/source_interference/data/experiments/agent-readability/fixed-samples" \
  --fetch-missing-test-sources
```

The fetch flag downloads only the selected BugsInPy test blobs from their
recorded fixed GitHub revisions and stores them under the benchmark cache.

Before any model request, dynamically qualify the selected conditions. For each
task, this command restores the exact prompted buggy source and requires it to
compile (or pass Python byte compilation) while still failing the released
trigger tests. It then constructs the corresponding transformed fixed source
from the benchmark's official fixed revision and requires both the trigger tests
and complete project regression suite to pass:

```bash
python -m readability_experiments.benchmark_eval.prevalidation_cli \
  --workspace "$PWD/artifacts/source_interference" \
  --input "$PWD/artifacts/source_interference/data/experiments/agent-readability/fixed-samples/pilot/tasks.jsonl" \
  --output "$PWD/artifacts/source_interference/data/experiments/agent-readability/dynamic-qualified/pilot"
```

The command is resumable and writes `prevalidation.jsonl`, full command logs,
`report.json`, and a filtered model-ready `tasks.jsonl`. Missing historical
environments, timeouts, compilation failures, non-preserved failures, and
regressions are explicit exclusions rather than model failures. The
`--trigger-tests-only` option exists for inexpensive pipeline debugging; formal
experiments should use the default full-suite policy.

### Lightweight executable repair dataset

The independent lightweight experiment uses the official HumanEvalPack/
HumanEvalFix Java and Python records and the benchmark's default
`HumanEvalFixTests` `instruct` prompt. The two languages share the same selected
problem numbers. Each record provides a buggy implementation, canonical repair,
and standalone tests, so validation does not require historical project
checkouts or Maven/Gradle environments. Each interference is still applied
independently to the original complete source shown to the model. Model output
is interpreted as the repaired continuation after the repeated callable
declaration, as in the official evaluator, rather than as a unified diff.

The checked-in small configuration selects 10 paired problem numbers with seed
`20260823` (20 base tasks). For every original or transformed candidate, the
builder requires the buggy version to fail and the corresponding canonical
version to pass. It records every rejection and command log, and writes only the
usable tasks to the model manifest:

```bash
python -m readability_experiments.lightweight_eval.build_cli \
  --count 10 \
  --seed 20260823 \
  --output "$PWD/artifacts/source_interference/data/experiments/agent-readability-lightweight/dataset"
```

The output contains `tasks.jsonl`, `report.json`, and
`validation/validation.jsonl`; detailed compiler and test output is under
`validation/logs/`. The resulting `tasks.jsonl` is accepted directly by the
same DeepSeek runner and uses standalone official tests for automatic scoring:

```bash
python -m readability_experiments.deepseek_cli run \
  --input artifacts/source_interference/data/experiments/agent-readability-lightweight/dataset/tasks.jsonl \
  --output-root results/experiments/source_interference/deepseek-lightweight \
  --models deepseek-v4-pro \
  --validation-timeout-seconds 30
```

### Official DeepSeek runner

The runner reads `DEEPSEEK_API_KEY` from the environment and calls only the
official `https://api.deepseek.com/chat/completions` endpoint. Supported model
IDs are `deepseek-v4-pro` and `deepseek-v4-flash`.

```bash
python -m readability_experiments.deepseek_cli smoke
```

The runner sends the documented provider defaults explicitly for reproducibility:
thinking enabled, reasoning effort high, temperature 1.0, and a 30,000-token
experimental output cap. DeepSeek ignores temperature in thinking mode. The
structured prompt smoke test stores one immutable run
directory containing `run.json`, `tasks.jsonl`, `responses.jsonl`, and
`summary.json`:

```bash
python -m readability_experiments.deepseek_cli prompt-smoke \
  --output-root results/experiments/source_interference/deepseek \
  --max-tokens 2048
```

Validated task files must contain `task_id` and `prompt`. Repair task files must
also carry the successful dynamic-prevalidation marker written by the preceding
command. Candidate inventories and merely static-validated manifests are
rejected because they do not yet contain executable oracles.
Prompts and expected answers are stored once in `tasks.jsonl`. Each response in
`responses.jsonl` contains only `task_id`, `answer`, `correct`, `raw_response`,
`usage`, `response_id`, and `model`. The complete reasoning content remains in
`raw_response`. Summary statistics are grouped by model, experiment, and
interference condition. The summary also pairs every transformed response with
the same model's original response and reports robust success, degradation,
improvement, persistent failure, and the degradation rate conditional on an
originally successful repair. A
stopped run can be continued with `--resume-run`; completed `(task_id, model)`
pairs are skipped. Defects4J and prepared BugsInPy repair responses are dynamically
validated by default. The runner restores the exact source shown in the prompt,
restricts the patch to the target production file, applies it, and runs every
released relevant test. BugsInPy validation uses an isolated copy of the official
buggy checkout (including the benchmark's fixed test files) and a prepared interpreter
under `artifacts/source_interference/data/benchmarks/envs/bugsinpy/<instance-id>`; the legacy pilot environment
`artifacts/source_interference/data/benchmarks/envs/python-<major.minor>` is also recognized. Missing per-instance
checkouts or environments are reported as infrastructure errors, never as incorrect
model answers. Evaluation checks patch scope and application, compilation,
released trigger tests, and the complete regression suite. The compatibility
field `correct` means that the released trigger tests pass and the complete
suite has no failures absent from the corresponding transformed-buggy baseline;
it is not a correctness claim beyond the benchmark oracle. Structured records expose `patch_applied`,
`compiled`, `trigger_tests_passed`, `regression_tests_passed`, and
`functional_success` in `evaluations.jsonl`, while full command output remains
in `evaluation-logs/`.

```bash
python -m readability_experiments.deepseek_cli run \
  --input artifacts/source_interference/data/experiments/agent-readability/dynamic-qualified/pilot/tasks.jsonl \
  --output-root results/experiments/source_interference/deepseek \
  --models deepseek-v4-pro
```

For the lower-cost DeepSeek V4 Flash run on the complete lightweight repair
dataset, use the provider's stable API model ID `deepseek-v4-flash`.  This
configuration disables thinking to match the existing V4 Pro experiment and
stores the run separately:

```bash
python -m readability_experiments.deepseek_cli run \
  --input artifacts/source_interference/data/experiments/agent-readability-lightweight/full-dataset/tasks.jsonl \
  --output-root results/experiments/source_interference/deepseek-v4-flash \
  --models deepseek-v4-flash \
  --thinking disabled \
  --reasoning-effort low \
  --max-tokens 30000 \
  --length-retries 1 \
  --request-retries 5 \
  --validation-timeout-seconds 30
```

Transient connection failures, HTTP 429 responses, and HTTP 5xx responses are
retried with bounded exponential backoff.  These transport retries are distinct
from `--length-retries` and are recorded in each response as
`transport_retry_history`.  Resume an interrupted run with the same input and
model configuration plus `--resume-run`; already saved task/model pairs are
not requested again.

Use `--skip-external-validation` only when response collection and test
execution intentionally need to be separated. A saved run can be evaluated
later without another API call:

```bash
python -m readability_experiments.deepseek_cli evaluate \
  --run-directory results/experiments/source_interference/deepseek/<name>/run-<timestamp>
```

### Groq Batch runner

The complementary open-weight model run uses Groq's official Batch API with
`openai/gpt-oss-120b`. The default configuration fixes high reasoning,
temperature 1.0, a 50,000-token completion cap, inclusion of the separate
reasoning field, batches of 1,000 requests, and a 24-hour completion window.
It reads `GROQ_API_KEY` from the environment. Prepare and submit the complete
HumanEvalPack run with:

```bash
python -m readability_experiments.groq_cli submit \
  --input artifacts/source_interference/data/experiments/agent-readability-lightweight/full-dataset/tasks.jsonl \
  --output-root results/experiments/source_interference/groq
```

The command prints the immutable run directory. Batch input files, the mapping
from Groq custom IDs to task IDs, and every remote batch ID are saved there
before the command exits. Submission is resumable with `--resume-run`. To
inspect the remote jobs without downloading responses:

```bash
python -m readability_experiments.groq_cli status \
  --run-directory results/experiments/source_interference/groq/tasks/run-<timestamp>
```

Once all jobs have completed, download the raw outputs and automatically run
the same standalone official tests used for DeepSeek:

```bash
python -m readability_experiments.groq_cli collect \
  --run-directory results/experiments/source_interference/groq/tasks/run-<timestamp> \
  --validation-timeout-seconds 30
```

`collect` is idempotent: downloaded provider files are retained, normalized
responses are rebuilt deterministically, and no model request is repeated.
Use `--skip-validation` only to separate response collection from local test
execution. `--prepare-only` on `submit` writes inspectable JSONL files without
making an API call.

If a provider-side failure leaves some requests without successful output,
resubmit only those request IDs in the same immutable run with:

```bash
python -m readability_experiments.groq_cli retry-missing \
  --run-directory results/experiments/source_interference/groq/tasks/run-<timestamp>
```

## Validation boundary

Java sources and generated classes are parsed with Tree-sitter Java; Python
sources and generated classes are validated with `ast.parse`. Output is written
atomically only if the complete run succeeds. This guarantees parse-level Java syntax,
not project-level compilation or strict semantic equivalence. Cross-file call sites and
override contracts cannot be resolved when complete classes are processed independently.

## Tests

```bash
python -m pytest -q -c tools/source_interference/pyproject.toml tools/source_interference/tests
```
