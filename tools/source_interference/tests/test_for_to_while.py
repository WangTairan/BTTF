from __future__ import annotations

import ast
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from readability_data.java_degradation.interferences.control_flow import (
    LowerForToWhile as JavaLowerForToWhile,
)
from readability_data.java_degradation.interferences.core.java import validate_java
from readability_data.python_degradation.core import Context
from readability_data.python_degradation.interferences.control_flow import (
    LowerForToWhile as PythonLowerForToWhile,
)

JAVA_SOURCE = b"""public class LoopExample {
  static int calculate(int limit) {
    int result = 0;
    for (int row = 0, width = limit; row < limit; row++, width--) {
      for (int column = 0; column < width; column++) {
        result += row + column;
      }
    }
    return result;
  }
}
"""

PYTHON_SOURCE = """def calculate(rows):
    result = []
    for row in rows:
        for left, right in row:
            if left < 0:
                continue
            if left == 9:
                break
            result.append(left + right)
    return result
"""


class ForToWhileTests(unittest.TestCase):
    def test_java_lowers_nested_classic_loops_deterministically(self) -> None:
        plugin = JavaLowerForToWhile()
        context = Context(17, "java-for")
        first = plugin.apply(JAVA_SOURCE, context)
        second = plugin.apply(JAVA_SOURCE, context)

        self.assertEqual(first, second)
        self.assertEqual(first.stats["classic_for_loops_found"], 2)
        self.assertEqual(first.stats["for_loops_lowered_to_while"], 2)
        self.assertNotIn(b"for (", first.content)
        self.assertEqual(first.content.count(b"while ("), 2)
        validate_java(first.content, "LoopExample", "lower-for-to-while")

    def test_java_lowers_enhanced_loop_and_skips_unsafe_classic_forms(self) -> None:
        source = b"""class Safety {
  void run(int[] values) {
    for (int value : values) { use(value); }
    enhanced: for (int value : values) { if (value == 1) continue enhanced; }
    for (String item : provider.fetch()) { use(item); }
    outer: for (int i = 0; i < 3; i++) { use(i); }
    for (int i = 0; i < 3; i++) { if (i == 1) continue; use(i); }
    for (int i = 0; i < 3;) { if (i == 1) continue; use(i++); }
  }
  void use(int value) {}
  void use(String value) {}
}
"""
        result = JavaLowerForToWhile().apply(source, Context(1, "java-safety"))

        self.assertEqual(result.stats["classic_for_loops_found"], 3)
        self.assertEqual(result.stats["for_loops_lowered_to_while"], 2)
        self.assertEqual(result.stats["for_loops_skipped_for_label"], 1)
        self.assertEqual(result.stats["for_loops_skipped_for_continue"], 1)
        self.assertEqual(result.stats["enhanced_for_loops_lowered_to_while"], 1)
        self.assertEqual(result.stats["enhanced_array_loops_lowered"], 1)
        self.assertEqual(result.stats["enhanced_for_loops_found"], 3)
        self.assertEqual(result.stats["enhanced_for_loops_skipped_for_label"], 1)
        self.assertEqual(
            result.stats["enhanced_for_loops_skipped_unknown_source_type"], 1
        )
        self.assertEqual(result.stats["enhanced_for_loops_untouched"], 2)
        validate_java(result.content, "Safety", "lower-for-to-while-safety")

    @unittest.skipUnless(shutil.which("javac"), "javac is not installed")
    def test_java_enhanced_arrays_and_iterables_preserve_observed_result(self) -> None:
        source = b"""import java.util.Arrays;
public class EnhancedLoopExample {
  static int iterableEvaluations;
  static Iterable<Integer> values() {
    iterableEvaluations++;
    return Arrays.asList(4, 5, 9);
  }
  static int calculate(int... input) {
    int result = 0;
    for (int value : input) {
      if (value == 2) continue;
      result += value;
    }
    for (long value : values()) {
      if (value == 9) break;
      result += value;
    }
    return result * 10 + iterableEvaluations;
  }
  public static void main(String[] args) {
    System.out.print(calculate(1, 2, 3));
  }
}
"""
        result = JavaLowerForToWhile().apply(
            source, Context(17, "java-enhanced-compile")
        )
        self.assertEqual(result.stats["enhanced_array_loops_lowered"], 1)
        self.assertEqual(result.stats["enhanced_iterable_loops_lowered"], 1)
        self.assertEqual(result.stats["for_loops_lowered_to_while"], 2)
        self.assertNotIn(b"for (", result.content)
        with tempfile.TemporaryDirectory() as directory:
            outputs = []
            for label, content in (("original", source), ("lowered", result.content)):
                location = Path(directory) / label
                location.mkdir()
                (location / "EnhancedLoopExample.java").write_bytes(content)
                subprocess.run(
                    ["javac", "-encoding", "UTF-8", "EnhancedLoopExample.java"],
                    cwd=location,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                completed = subprocess.run(
                    ["java", "EnhancedLoopExample"],
                    cwd=location,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                outputs.append(completed.stdout)
            self.assertEqual(outputs[0], outputs[1])

    def test_python_lowers_nested_loops_and_preserves_observed_result(self) -> None:
        plugin = PythonLowerForToWhile()
        context = Context(17, "python-for")
        first = plugin.apply(PYTHON_SOURCE, context)
        second = plugin.apply(PYTHON_SOURCE, context)

        self.assertEqual(first, second)
        self.assertEqual(first.stats["synchronous_for_loops_found"], 2)
        self.assertEqual(first.stats["for_loops_lowered_to_while"], 2)
        self.assertFalse(
            any(
                isinstance(node, ast.For) for node in ast.walk(ast.parse(first.content))
            )
        )

        original_namespace: dict[str, object] = {}
        lowered_namespace: dict[str, object] = {}
        exec(PYTHON_SOURCE, original_namespace)
        exec(first.content, lowered_namespace)
        rows = [[(-1, 2), (2, 3)], [(9, 1), (4, 5)], [(6, 7)]]
        self.assertEqual(
            original_namespace["calculate"](rows),
            lowered_namespace["calculate"](rows),
        )

    def test_python_skips_for_else_comments_single_line_and_async(self) -> None:
        source = """def choose(values):
    for value in values:
        pass
    else:
        return None

def documented(values):
    for value in values:
        # Keep this explanation attached to the loop.
        print(value)

def compact(values):
    for value in values: print(value)

async def consume(stream):
    async for value in stream:
        print(value)
"""
        result = PythonLowerForToWhile().apply(source, Context(1, "python-safety"))

        self.assertEqual(result.content, source)
        self.assertEqual(result.stats["synchronous_for_loops_found"], 3)
        self.assertEqual(result.stats["for_loops_skipped_for_else"], 1)
        self.assertEqual(result.stats["for_loops_skipped_for_comment"], 1)
        self.assertEqual(result.stats["for_loops_skipped_for_single_line_suite"], 1)
        self.assertEqual(result.stats["async_for_loops_untouched"], 1)

    @unittest.skipUnless(shutil.which("javac"), "javac is not installed")
    def test_java_result_compiles_and_preserves_observed_result(self) -> None:
        source = JAVA_SOURCE.replace(
            b"  static int calculate",
            b"  public static void main(String[] args) { "
            b"System.out.print(calculate(5)); }\n  static int calculate",
        )
        result = JavaLowerForToWhile().apply(source, Context(17, "java-compile"))
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "original"
            lowered = Path(directory) / "lowered"
            original.mkdir()
            lowered.mkdir()
            (original / "LoopExample.java").write_bytes(source)
            (lowered / "LoopExample.java").write_bytes(result.content)
            outputs = []
            for location in (original, lowered):
                subprocess.run(
                    ["javac", "-encoding", "UTF-8", "LoopExample.java"],
                    cwd=location,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                completed = subprocess.run(
                    ["java", "LoopExample"],
                    cwd=location,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                outputs.append(completed.stdout)
            self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
