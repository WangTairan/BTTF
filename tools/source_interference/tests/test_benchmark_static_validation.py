from __future__ import annotations

import unittest

from readability_experiments.benchmark_eval.static_validation import (
    _python_changed_class,
    summarize,
)


class StaticValidationTest(unittest.TestCase):
    def test_python_changed_class_uses_most_changed_lines(self) -> None:
        before = """\
class Small:
    value = 1

class Main:
    def run(self):
        return 1
"""
        after = """\
class Small:
    value = 2

class Main:
    def run(self):
        value = 3
        return value + 4
"""
        self.assertEqual(_python_changed_class(before, after), "Main")

    def test_python_module_only_change_is_not_class_level(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not touch"):
            _python_changed_class("value = 1\n", "value = 2\n")

    def test_summary_counts_tasks_and_conditions(self) -> None:
        report = summarize(
            [
                {
                    "benchmark": "example",
                    "status": "usable",
                    "conditions": [
                        {"interference": "one", "status": "usable"},
                        {"interference": "two", "status": "not_applicable"},
                    ],
                },
                {"benchmark": "example", "status": "source_error"},
            ],
            7,
        )
        self.assertEqual(report["usable_task_count"], 1)
        self.assertEqual(report["usable_condition_count"], 1)
        self.assertEqual(
            report["task_status_by_benchmark"]["example"]["source_error"], 1
        )


if __name__ == "__main__":
    unittest.main()
