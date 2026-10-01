# Source-interference tool: detailed guide

This guide covers source generation, not primary-model feature selection.
Dataset generation refuses existing output paths;
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
