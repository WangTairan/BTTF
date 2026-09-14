from __future__ import annotations

import unittest

from readability_experiments.deepseek_cli import (
    _check_prompt_smoke,
    _prompt_smoke_tasks,
)
from readability_experiments.prompts import (
    behavior_prediction_prompt,
    benchmark_repair_prompt,
)


class PromptTests(unittest.TestCase):
    def test_language_is_embedded_in_sentence(self) -> None:
        prompt = behavior_prediction_prompt(
            language="Java",
            source_path="A.java",
            source_code="class A {}",
            harness_code="class Main {}",
        )
        self.assertIn("You are given Java source code", prompt)
        self.assertNotIn("Language: Java", prompt)

    def test_prompt_smoke_has_both_languages_and_experiments(self) -> None:
        tasks = _prompt_smoke_tasks()
        self.assertEqual(len(tasks), 4)
        self.assertEqual(
            {task["experiment"] for task in tasks},
            {
                "behavior-prediction",
                "test-guided-repair",
            },
        )

    def test_behavior_check_requires_exact_stdout(self) -> None:
        task = _prompt_smoke_tasks()[0]
        self.assertTrue(_check_prompt_smoke(task, '{"stdout_lines":["17"]}')[0])
        self.assertFalse(_check_prompt_smoke(task, '{"stdout_lines":["17",""]}')[0])

    def test_repair_check_accepts_optional_markdown_fence(self) -> None:
        task = _prompt_smoke_tasks()[2]
        response = """```diff
--- a/Calculator.java
+++ b/Calculator.java
@@ -1 +1 @@
-        return left - right;
+        return left + right;
```"""
        self.assertTrue(_check_prompt_smoke(task, response)[0])

    def test_benchmark_repair_prompt_is_compact_and_does_not_reveal_benchmark(
        self,
    ) -> None:
        prompt = benchmark_repair_prompt(
            language="Java",
            source_path="src/Demo.java",
            buggy_source="class Demo {}",
            test_code="void fails() {}",
            failure_output="expected 2 but was 1",
        )
        self.assertIn("Relevant failing test code:", prompt)
        self.assertIn("Observed test failure:", prompt)
        self.assertNotIn("Defects4J", prompt)
        self.assertNotIn("preserve the existing readability", prompt)

    def test_benchmark_repair_prompt_omits_unavailable_failure_section(self) -> None:
        prompt = benchmark_repair_prompt(
            language="Python",
            source_path="demo.py",
            buggy_source="value = 1",
            test_code="def test_value(): assert value == 2",
        )
        self.assertNotIn("Observed test failure:", prompt)


if __name__ == "__main__":
    unittest.main()
