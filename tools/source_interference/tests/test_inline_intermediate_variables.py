from __future__ import annotations

import ast
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from readability_data.java_degradation.interferences.core.java import validate_java
from readability_data.java_degradation.interferences.data_flow import (
    InlineIntermediateVariables as JavaInline,
)
from readability_data.python_degradation.core import Context
from readability_data.python_degradation.interferences.data_flow import (
    InlineIntermediateVariables as PythonInline,
)

JAVA_SOURCE = b"""public class InlineExample {
  int calculate(int input) { return input + 1; }
  int first() { int firstValue = calculate(10 + 1); return firstValue; }
  int second() { int secondValue = calculate(20 + 2); return secondValue; }
  int third() { int thirdValue = calculate(30 + 3); return thirdValue; }
  int fourth() { int fourthValue = calculate(40 + 4); return fourthValue; }
  int fifth() { int fifthValue = calculate(50 + 5); return fifthValue; }
}
"""

PYTHON_SOURCE = """class InlineExample:
    def calculate(self, input_value):
        return input_value + 1

    def first(self):
        first_value = self.calculate(10 + 1)
        return first_value

    def second(self):
        second_value = self.calculate(20 + 2)
        return second_value

    def third(self):
        third_value = self.calculate(30 + 3)
        return third_value

    def fourth(self):
        fourth_value = self.calculate(40 + 4)
        return fourth_value

    def fifth(self):
        fifth_value = self.calculate(50 + 5)
        return fifth_value
"""


class InlineIntermediateVariablesTests(unittest.TestCase):
    def test_java_inlines_all_eligible_variables_and_remains_parseable(self):
        context = Context(17, "java-inline")
        first = JavaInline().apply(JAVA_SOURCE, context)
        second = JavaInline().apply(JAVA_SOURCE, context)

        self.assertEqual(first, second)
        self.assertEqual(first.stats["intermediate_variables_available"], 5)
        self.assertEqual(first.stats["intermediate_variables_inlined"], 5)
        self.assertEqual(first.stats["identifier_references_replaced"], 5)
        self.assertEqual(first.stats["target_fraction_percent"], 100)
        validate_java(first.content, "InlineExample", "inline-intermediates")

    def test_python_inlines_all_eligible_variables_and_remains_parseable(self):
        context = Context(17, "python-inline")
        first = PythonInline().apply(PYTHON_SOURCE, context)
        second = PythonInline().apply(PYTHON_SOURCE, context)

        self.assertEqual(first, second)
        self.assertEqual(first.stats["intermediate_variables_available"], 5)
        self.assertEqual(first.stats["intermediate_variables_inlined"], 5)
        self.assertEqual(first.stats["identifier_references_replaced"], 5)
        self.assertEqual(first.stats["target_fraction_percent"], 100)
        ast.parse(first.content)

    def test_unsafe_or_repeated_variables_are_not_candidates(self):
        java = b"""class Safety {
  int run(boolean enabled) {
    int repeated = call();
    int reassigned = call();
    reassigned = 3;
    int delayed = call();
    log();
    int conditional = call();
    if (enabled) { return conditional; }
    return repeated + repeated + reassigned + delayed + delayed;
  }
  int call() { return 1; }
  void log() {}
}
"""
        python = """class Safety:
    def run(self, enabled):
        repeated = self.call()
        reassigned = self.call()
        reassigned = 3
        delayed = self.call()
        self.log()
        conditional = self.call()
        if enabled:
            return conditional
        return repeated + repeated + reassigned + delayed + delayed
"""
        java_result = JavaInline().apply(java, Context(1, "safe"))
        python_result = PythonInline().apply(python, Context(1, "safe"))
        self.assertEqual(java_result.stats["intermediate_variables_available"], 0)
        self.assertEqual(python_result.stats["intermediate_variables_available"], 0)
        self.assertEqual(java_result.content, java)
        self.assertEqual(python_result.content, python)

    @unittest.skipUnless(shutil.which("javac"), "javac is not installed")
    def test_java_result_compiles(self):
        result = JavaInline().apply(JAVA_SOURCE, Context(17, "java-inline"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "InlineExample.java"
            path.write_bytes(result.content)
            subprocess.run(
                ["javac", "-encoding", "UTF-8", path.name],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )


if __name__ == "__main__":
    unittest.main()
