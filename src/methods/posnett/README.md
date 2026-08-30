# Posnett

This package implements the Posnett, Hindle, and Devanbu readability score
published in *A Simpler Model of Software Readability* (MSR 2011).

## Model

The implemented score is the published logistic probability:

```text
readability = 1 / (1 + exp(-z))
z = 8.87 - 0.033 * V + 0.40 * Lines - 1.5 * H
```

- `V`: Halstead volume extracted from lexical operators and operands. Java
  uses the reproduction's fixed lexer; the optional Python transfer path uses
  the Python standard-library tokenizer.
- `Lines`: source lines, including comment lines.
- `H`: byte entropy of the source snippet.

`score` and `probability` are the same value in `[0, 1]`; higher values
indicate predicted higher readability. The JetBrains files include derived
binary metric columns with opposite encodings between their snippet and
human-score tables, so those columns are retained as metadata rather than used
to orient the continuous Posnett result.

For binary-labeled evaluation, the shared runner reports best-threshold MCC for
JetBrains and records the selected threshold in `summary.json`. This is an
experimental separability setting; the published logistic classifier's standard
decision threshold is `score >= 0.5`.

## Scope

The published model was built from and evaluated on small Java code snippets.
Java remains the standard reproduction setting. For the constructed Python
experiment, the published coefficients are kept fixed while Halstead tokens
are obtained with Python's standard tokenizer. This is reported as a
cross-language transfer experiment, not as a reproduction of a published
Python Posnett model.

The model is intended for short snippets. Scores over complete classes, such
as the Schnappinger samples, are useful as an exploratory baseline but exceed
the original validation granularity.

## Reference

D. Posnett, A. Hindle, and P. Devanbu, *A Simpler Model of Software
Readability*, MSR 2011, DOI: `10.1145/1985441.1985454`.

## Command

```bash
python -m src.experiments.evaluate_method datasets/jetbrains --method posnett
python -m src.experiments.evaluate_method datasets/schnappinger --method posnett
```
