from __future__ import annotations

import unittest

from readability_experiments.benchmark_eval.diagnostics import (
    _method_names,
    _python_methods,
)


class BenchmarkDiagnosticsTests(unittest.TestCase):
    def test_pytest_selector_uses_method_not_class(self) -> None:
        self.assertEqual(
            _method_names(["pytest tests/test_demo.py::DemoTests::test_failure"]),
            {"test_failure"},
        )

    def test_unittest_class_selector_extracts_class_context(self) -> None:
        source = (
            """class DemoTests:\n    def test_failure(self):\n        assert False\n"""
        )
        names = _method_names(["python -m unittest tests.test_demo.DemoTests"])
        self.assertEqual(names, {"DemoTests"})
        self.assertEqual(_python_methods(source, names), [source.rstrip()])


if __name__ == "__main__":
    unittest.main()
