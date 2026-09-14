from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from readability_experiments.lightweight_eval.validator import (
    LightweightPatchValidator,
    completion_source,
    recount_diff_hunks,
)
from readability_experiments.prompts import benchmark_repair_prompt


class LightweightPatchValidatorTests(unittest.TestCase):
    def test_python_completion_selects_target_function_not_trailing_check_block(
        self,
    ) -> None:
        prefix = "def has_close_elements(numbers, threshold):\n"
        answer = """The first snippet illustrates the bug.
```python
distance = left - right
```
The corrected implementation is:
```python
def has_close_elements(numbers, threshold):
    return any(abs(a - b) < threshold for a in numbers for b in numbers if a != b)
```
Verification:
```python
def check(candidate):
    assert candidate([1.0, 1.1], 0.2)
```
"""
        source = completion_source(answer, prefix, "python")
        self.assertTrue(source.startswith("def has_close_elements"))
        self.assertNotIn("def check", source)

    def test_official_completion_is_joined_without_losing_indentation(self) -> None:
        self.assertEqual(
            completion_source("\n    return value + 1", "def add(value):\n", "python"),
            "def add(value):\n    return value + 1\n",
        )

    def test_chat_fenced_full_source_is_accepted(self) -> None:
        self.assertEqual(
            completion_source(
                "Explanation.\n```python\ndef add(value):\n    return value + 1\n```",
                "def add(value):\n",
                "python",
            ),
            "def add(value):\n    return value + 1\n",
        )

    def test_java_completion_discards_repeated_main_harness(self) -> None:
        answer = """Explanation.\n```java
import java.util.*;
class Solution { int add(int a, int b) { return a + b; } }
public class Main { public static void main(String[] args) {} }
```"""
        self.assertEqual(
            completion_source(
                answer,
                "import java.util.*;\nclass Solution { int add(int a, int b) {",
                "java",
            ),
            "import java.util.*;\nclass Solution { int add(int a, int b) { return a + b; } }\n",
        )
        self.assertEqual(
            completion_source(
                "```java\nclass Solution {}\n```",
                "import java.util.*;\nclass Solution { int add() {",
                "java",
            ),
            "import java.util.*;\nclass Solution {}\n",
        )
        self.assertEqual(
            completion_source(
                "```python\nold + 1\n```\nFixed:\n```python\ndef add(value):\n    return value + 1\n```",
                "def add(value):\n",
                "python",
            ),
            "def add(value):\n    return value + 1\n",
        )

    def test_official_completion_is_executed(self) -> None:
        prefix = "def add(left, right):\n"
        test = "def check(candidate):\n    assert candidate(3, 2) == 5\ncheck(add)"
        with tempfile.TemporaryDirectory() as directory:
            validator = LightweightPatchValidator(Path(directory), timeout_seconds=10)
            result = validator.validate(
                {
                    "task_id": "official-python",
                    "language": "python",
                    "source_path": "solution.py",
                    "test_code": test,
                    "completion_prefix": prefix,
                    "expected_kind": "lightweight_completion_validation",
                },
                "\n    return left + right",
                "test-model",
            )
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["correct"])

    def test_test_timeout_is_a_recorded_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            validator = LightweightPatchValidator(Path(directory), timeout_seconds=0.1)
            result = validator.execute_source(
                {"language": "python", "test_code": "while True:\n    pass"},
                "def answer():\n    return 42\n",
            )
        self.assertTrue(result["compiled"])
        self.assertFalse(result["tests_passed"])
        self.assertTrue(result["test_timed_out"])
        self.assertEqual(result["test_exit_code"], 124)

    def test_model_hunk_counts_are_recounted(self) -> None:
        patch = "--- a/x.py\n+++ b/x.py\n@@ -20,7 +20,7 @@\n-old\n+new\n"
        self.assertIn("@@ -20,1 +20,1 @@", recount_diff_hunks(patch))

    def test_python_source_and_patch_are_checked_by_official_style_test(self) -> None:
        buggy = "def add(left, right):\n    return left - right\n"
        test = "def check(candidate):\n    assert candidate(3, 2) == 5\ncheck(add)"
        with tempfile.TemporaryDirectory() as directory:
            validator = LightweightPatchValidator(Path(directory), timeout_seconds=10)
            task = {
                "task_id": "python-smoke",
                "language": "python",
                "source_path": "solution.py",
                "test_code": test,
                "prompt": benchmark_repair_prompt(
                    language="Python",
                    source_path="solution.py",
                    buggy_source=buggy,
                    test_code=test,
                ),
            }
            self.assertFalse(validator.execute_source(task, buggy)["tests_passed"])
            patch = (
                "--- a/solution.py\n+++ b/solution.py\n"
                "@@ -1,2 +1,2 @@\n"
                " def add(left, right):\n"
                "-    return left - right\n"
                "+    return left + right\n"
            )
            result = validator.validate(task, patch, "test-model")
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["correct"])

    def test_stale_line_number_and_trailing_fence_are_tolerated(self) -> None:
        buggy = "def add(left, right):\n    return left - right\n"
        test = "def check(candidate):\n    assert candidate(3, 2) == 5\ncheck(add)"
        with tempfile.TemporaryDirectory() as directory:
            validator = LightweightPatchValidator(Path(directory), timeout_seconds=10)
            task = {
                "task_id": "python-offset",
                "language": "python",
                "source_path": "solution.py",
                "test_code": test,
                "prompt": benchmark_repair_prompt(
                    language="Python",
                    source_path="solution.py",
                    buggy_source=buggy,
                    test_code=test,
                ),
            }
            patch = (
                "--- a/solution.py\n+++ b/solution.py\n"
                "@@ -99,7 +99,7 @@\n"
                "-    return left - right\n"
                "+    return left + right\n```"
            )
            result = validator.validate(task, patch, "test-model")
        self.assertEqual(result["status"], "passed")

    @unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK required")
    def test_java_source_shares_imports_with_official_main_harness(self) -> None:
        source = "import java.util.*;\nclass Solution { static int size(List<Integer> x) { return x.size(); } }"
        test = "public class Main { public static void main(String[] x) { if (Solution.size(Arrays.asList(1, 2)) != 2) throw new AssertionError(); } }"
        with tempfile.TemporaryDirectory() as directory:
            validator = LightweightPatchValidator(Path(directory), timeout_seconds=10)
            result = validator.execute_source(
                {"language": "java", "test_code": test}, source
            )
        self.assertTrue(result["compiled"])
        self.assertTrue(result["tests_passed"])


if __name__ == "__main__":
    unittest.main()
