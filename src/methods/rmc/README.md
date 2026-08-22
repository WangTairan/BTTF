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

The reported control score uses one capacity-normalized recovery-error formula:

```text
RMC = 1 - sum(error_penalty_i * (1 - similarity_i)) / sum(capacity_i)
```

Method bodies use capacity 2.0 and error penalty 1.0. Exception-handling bodies
use capacity and error penalty 0.5; `if`, loop, `switch`, and other control
bodies use capacity and error penalty 1.0. A mask occupying proportion
`r = mask_tokens / source_tokens` receives contribution weight `4r(1-r)`.
This continuously reduces the influence of both very small masks and masks that
hide nearly the entire sample. For samples with at least 30 non-blank lines,
the score is reduced by 0.10 when the number of non-method control regions
divided by LOC is below 0.15.
This sparse-control penalty prevents long samples with little observable
control logic from receiving an inflated readability score.

Recovery supports the original keyed-JSON prompt and two generalist-developer
3-shot variants: `generalist_negative_3shot` and
`generalist_positive_3shot`. The 3-shot prompts target the current single-mask
experiments and require exactly one `mask_1` value.

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
separately. Only candidates containing at least `3` Java lexical
tokens are retained by default (`--ast-min-tokens`). The reported score uses
single holes, so `--max-combination-size` defaults to `1`. Higher values remain
available for explicit combination experiments.
Combination holes are deterministically sampled per `(granularity, combination
size)` stratum only when `--max-samples-per-stratum` is set. By default the
budget is unlimited and all eligible combinations are retained; if a budget is
set, `--sampling-seed 42` controls the deterministic sample.
This keeps very small holes out of the experiment without using lines as the
code unit and without splitting a larger structure merely to fit an upper
bound. A loop is never split into its header and body as a control-flow
candidate. Nested legal AST holes are retained alongside their parent control
hole. Candidate holes are grouped into `control` and `statement`
granularities. Multi-hole masks combine only non-overlapping holes in the same
granularity when explicitly enabled with `--max-combination-size`; the number
of eligible candidates in the selected granularity does not disable
combinations.
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
results/methods/rmc/<dataset>/<model>/
```
