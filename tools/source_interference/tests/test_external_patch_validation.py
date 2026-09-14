from __future__ import annotations

import unittest
from pathlib import Path

from readability_experiments.benchmark_eval.external_validation import (
    ExternalPatchValidator,
    _patch_strip_level,
    normalize_unified_diff,
    patch_paths,
    source_from_benchmark_prompt,
)
from readability_experiments.prompts import benchmark_repair_prompt


class ExternalPatchValidationTests(unittest.TestCase):
    def test_extracts_the_exact_source_variant_from_the_prompt(self) -> None:
        prompt = benchmark_repair_prompt(
            language="Java",
            source_path="src/Demo.java",
            buggy_source="class Demo {\n    int value = 1;\n}",
            test_code="void fails() { assertEquals(2, new Demo().value); }",
            failure_output="expected:<2> but was:<1>",
        )
        self.assertEqual(
            source_from_benchmark_prompt(prompt),
            "class Demo {\n    int value = 1;\n}",
        )

    def test_normalizes_fenced_diff_and_finds_its_scope(self) -> None:
        answer = """```diff
--- a/src/Demo.java
+++ b/src/Demo.java
@@ -1 +1 @@
-old
+new
```"""
        normalized = normalize_unified_diff(answer)
        self.assertFalse(normalized.startswith("```"))
        self.assertEqual(patch_paths(normalized), {"src/Demo.java"})
        self.assertEqual(_patch_strip_level(normalized), 1)

    def test_plain_unified_diff_paths_use_zero_strip_level(self) -> None:
        value = "--- src/Demo.java\n+++ src/Demo.java\n"
        self.assertEqual(patch_paths(value), {"src/Demo.java"})
        self.assertEqual(_patch_strip_level(value), 0)

    def test_detects_a_patch_that_touches_more_than_the_target(self) -> None:
        value = """--- a/src/Demo.java
+++ b/src/Demo.java
--- a/test/DemoTest.java
+++ b/test/DemoTest.java
"""
        self.assertEqual(patch_paths(value), {"src/Demo.java", "test/DemoTest.java"})

    def test_bugsinpy_pytest_command_uses_prepared_interpreter(self) -> None:
        python = Path("/prepared/python")
        self.assertEqual(
            ExternalPatchValidator._bugsinpy_test_command(
                "pytest -q tests/test_demo.py::test_case", python
            ),
            ("/prepared/python", "-m", "pytest", "-q", "tests/test_demo.py::test_case"),
        )

    def test_bugsinpy_python_command_uses_prepared_interpreter(self) -> None:
        python = Path("/prepared/python")
        self.assertEqual(
            ExternalPatchValidator._bugsinpy_test_command(
                "python -m unittest tests.test_demo", python
            ),
            ("/prepared/python", "-m", "unittest", "tests.test_demo"),
        )

    def test_bugsinpy_rejects_shell_commands(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported BugsInPy test command"):
            ExternalPatchValidator._bugsinpy_test_command(
                "bash run-tests.sh", Path("/prepared/python")
            )

    def test_bugsinpy_expands_released_semicolon_separated_tests(self) -> None:
        commands = ExternalPatchValidator._bugsinpy_test_commands(
            "pytest tests/test_a.py::test_a;pytest tests/test_b.py::test_b",
            Path("/prepared/python"),
        )
        self.assertEqual(
            commands,
            (
                ("/prepared/python", "-m", "pytest", "tests/test_a.py::test_a"),
                ("/prepared/python", "-m", "pytest", "tests/test_b.py::test_b"),
            ),
        )


if __name__ == "__main__":
    unittest.main()
