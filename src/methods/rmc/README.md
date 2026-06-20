# RMC

Recursive Masking Complexity masks code control regions, asks the LLM to return
exact replacements for each hidden region, and scores the hidden regions
directly.

Java/code runs use `java_ast_stratified_v8` masking. A hole removes one parsed
Java statement or one explicit control-flow body instead of an arbitrary line
interval. In the control granularity, headers remain visible and the candidate
set is:

- `MethodDeclaration` and `ConstructorDeclaration` bodies
- `IfBranch` for `then` and `else` bodies
- `ForStatement`, `WhileStatement`, and `DoStatement` bodies
- each `SwitchCase` body
- `TryBody`, `CatchBody`, and `FinallyBody`

The statement granularity contains ordinary Java statements such as field and
local declarations, returns, throws, and statement expressions.

The Dorn runner is the exception: the original Dorn dataset contains CUDA,
Java, and Python snippets, and many snippets are fragments rather than parseable
compilation units. `src.methods.rmc.runners.dorn` therefore uses
`dorn_fragment_control_v2`, a language-tolerant matcher that uses braces for
Java/CUDA snippets and indentation for Python snippets. It extracts control
bodies and method/function bodies while keeping headers visible. It keeps the
same RMC output schema and reports the strategy and language coverage in
`config.json` and `summary.json`.

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

## Smoke Commands

```bash
python -m src.methods.rmc.runners.mbjp --mock-recover --ast-granularity control --limit 1
python -m src.methods.rmc.runners.dorn --mock-recover --ast-granularity control --limit 1
python -m src.methods.rmc.runners.schnappinger --mock-recover --task-id 'Schnappinger/aoi/artofillusion.animation.distortion.CustomDistortion'
python -m src.methods.rmc.runners.jetbrains --mock-recover --limit 1
```

Results use:

```text
output/rmc/<dataset>/<model>/
```
