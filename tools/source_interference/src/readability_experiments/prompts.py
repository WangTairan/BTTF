from __future__ import annotations


def behavior_prediction_prompt(
    *, language: str, source_path: str, source_code: str, harness_code: str
) -> str:
    return f"""You are given {language} source code and a deterministic execution harness.

Predict the exact standard output produced by running the harness with the provided source code. Do not modify the code or explain your reasoning.

The target source file is {source_path}.

Source code:

```
{source_code}
```

Execution harness:

```
{harness_code}
```

Represent standard output as an array of lines with the line terminators removed. Return exactly one JSON object in the following form:

{{"stdout_lines": ["<first line>", "<second line>"]}}

Use an empty array if nothing is printed. Preserve all spaces, punctuation, escaping, and capitalization within each line. Do not return Markdown or any text outside the JSON object."""


def test_guided_repair_prompt(
    *,
    language: str,
    source_path: str,
    buggy_source: str,
    test_source: str,
    test_command: str,
    failure_output: str,
) -> str:
    return f"""You are given a {language} source file containing exactly one intentionally introduced defect, together with the relevant failing tests.

Produce the smallest source-code change that fixes the defect. Do not reformat, rename, simplify, or otherwise modify unrelated code. Preserve the existing readability and coding style, even when the code appears unnecessarily complex.

The target source file is {source_path}.

Buggy source:

```
{buggy_source}
```

Relevant test source:

```
{test_source}
```

The tests are executed with the following command:

```
{test_command}
```

The execution produces the following failing-test output:

```
{failure_output}
```

Return only a unified diff that applies to the target source file. Do not include explanations, Markdown fences, or any text outside the unified diff."""


def benchmark_repair_prompt(
    *,
    language: str,
    source_path: str,
    buggy_source: str,
    test_code: str,
    failure_output: str = "",
) -> str:
    language_tag = "java" if language.lower() == "java" else "python"
    failure_section = (
        f"""

Observed test failure:

```text
{failure_output}
```"""
        if failure_output
        else ""
    )
    return f"""Fix the defect in the following {language} source file.

Change only the target file. Make the smallest necessary correction and do not modify unrelated code.

Target file: {source_path}

Source code:

```{language_tag}
{buggy_source}
```

Relevant failing test code:

```{language_tag}
{test_code}
```{failure_section}

Return only a unified diff for the target file. Do not include explanations or Markdown fences."""


def humanevalfix_tests_instruct_prompt(
    *,
    buggy_source: str,
    test_code: str,
    entry_point: str,
    completion_prefix: str,
) -> str:
    """Reproduce HumanEvalPack's default HumanEvalFixTests prompt."""
    context = buggy_source + "\n" + test_code
    instruction = f"Fix bugs in {entry_point}."
    return (context + "\n" + instruction + "\n\n" + completion_prefix).strip()
