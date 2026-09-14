from __future__ import annotations

import ast
import unittest

from readability_experiments.benchmark_eval.class_source import (
    transform_java_class,
    transform_python_class,
)


class BenchmarkClassSourceTests(unittest.TestCase):
    def test_replaces_only_selected_python_class(self) -> None:
        source = "before = 1\nclass Target:\n    value = 2\n\nafter = 3\n"
        result = transform_python_class(
            source,
            "Target",
            lambda unit: unit.replace("value = 2", "value = 4"),
        )
        self.assertIn("before = 1", result)
        self.assertIn("value = 4", result)
        self.assertIn("after = 3", result)
        ast.parse(result)

    def test_replaces_only_selected_java_class(self) -> None:
        source = b"package x; class First {} public class Target { int n = 2; }"
        result = transform_java_class(
            source,
            "Target",
            lambda unit: unit.replace(b"n = 2", b"n = 4"),
        )
        self.assertIn(b"class First {}", result)
        self.assertIn(b"n = 4", result)


if __name__ == "__main__":
    unittest.main()
