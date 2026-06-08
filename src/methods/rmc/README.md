# RMC

Recursive Masking Complexity implementation and its commands live entirely in
this package.

RMC asks a configured recovery model to complete missing portions and averages
recovery similarity over the generated masks.

Java/code runs use `java_ast_stratified_v7` masking. A hole removes one complete
parsed Java node or one explicit control-flow slot instead of an arbitrary
line interval. The candidate set is:

- `MethodDeclaration` and `ConstructorDeclaration`
- `FieldDeclaration` and `LocalVariableDeclaration`
- `ReturnStatement`, `ThrowStatement`, and `StatementExpression`
- `IfCondition`, `IfBranch` for `then` and `else` slots
- complete `ForStatement`, `WhileStatement`, and `DoStatement`
- complete `SwitchStatement`
- complete `TryStatement`, including its `catch` and `finally` clauses

The Dorn runner is the exception: the original Dorn dataset contains CUDA,
Java, and Python snippets, and many snippets are fragments rather than parseable
compilation units. `src.methods.rmc.runners.dorn` therefore uses
`java_fragment_control_v1`, a language-tolerant token/bracket matcher for
control structures, instead of the Java AST parser. It keeps the same RMC
output schema and reports the strategy and language coverage in `config.json`
and `summary.json`.

Java experiments run one AST granularity at a time. The default is
`--ast-granularity control`; `statement` must be run separately and reported
separately. Only candidates containing at least `8` Java lexical
tokens are retained by default (`--ast-min-tokens`). A multi-hole mask contains
at most `3` holes by default (`--max-combination-size`). Single holes are
retained in full.
Combination holes are deterministically sampled per `(granularity, combination
size)` stratum only when `--max-samples-per-stratum` is set. By default the
budget is unlimited and all eligible combinations are retained; if a budget is
set, `--sampling-seed 42` controls the deterministic sample.
This keeps very small holes out of the experiment without using lines as the
code unit and without splitting a larger structure merely to fit an upper
bound. A loop is never split into its header and body as a control-flow
candidate. Nested legal AST holes are retained alongside their parent control
hole. Candidate holes are grouped into `control` and `statement`
granularities. Multi-hole masks combine only non-overlapping holes in the
same granularity, up to `--max-combination-size`; the number of eligible
candidates in the selected granularity does not disable combinations. The Java
task score is the equal mean of its available combination-size strata within
the selected granularity, rather than a flat average over all generated holes.
The sequence
parameters `nmin`, `nmax`, `lmin`, and `lmax` are not used for Java AST mask
generation.

The separate `java_ast_prefix_v1` variant does not insert masks. It builds
prefix-continuation tasks at the same `control` or `statement` AST
granularities: the model receives `source[:cut]` and must continue the full
Java code. Prefix cut points normally use AST candidate ends, so each later
task reveals more code. If no end cut point exists because a candidate reaches
EOF, candidate starts are used as a fallback.

Natural-language runs use semantic units rather than equal partitions. The CLEAR
runner supports `--nl-granularity sentence` and `--nl-granularity paragraph`,
with default `--nl-min-words 8`. Sentence runs may combine up to three sentence
holes, sampled with the same `--max-combination-size`,
`--max-samples-per-stratum`, and `--sampling-seed` controls used by Java AST
runs.

Commands:

```bash
python -m src.methods.rmc.runners.file examples/cognascore_example.java --mock-recover
python -m src.methods.rmc.runners.mbjp --mock-recover --ast-granularity control --limit 1
python -m src.methods.rmc.runners.dorn --mock-recover --ast-granularity control --limit 1
python -m src.methods.rmc.runners.mbjp_prefix --mock-recover --ast-granularity statement --limit 1
python -m src.methods.rmc.runners.clear --mock-recover --nl-granularity sentence --limit 1
python -m src.methods.rmc.runners.scalabrino_prefix --mock-recover --ast-granularity statement --limit 1
python -m src.methods.rmc.runners.schnappinger --mock-recover --task-id 'Schnappinger/aoi/artofillusion.animation.distortion.CustomDistortion'
python -m src.methods.rmc.runners.jetbrains --mock-recover --limit 1
python -m src.methods.rmc.runners.spearman output/rmc_masked/<dataset>/<model>
```

The dataset runner performs recovery once. Its saved results can then be
evaluated without additional recovery calls using `--similarity sequence`,
`--similarity exact_match`, `--similarity edit`, `--similarity token_jaccard`,
`--similarity token_cosine`, `--similarity bleu`, `--similarity rouge_l`, or
`--similarity cosine`. For stratified Java AST runs, report the
`official:ast_strata` row.

Results use:

```text
output/rmc_masked/<dataset>/<model>/  # Java/code
output/rmc_prefix/<dataset>/<model>/  # Java prefix/code
output/rmc_natural_language/<dataset>/<model>/  # natural language
```
