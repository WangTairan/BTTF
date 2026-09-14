import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from readability_data.java_degradation.interferences.core.base import (
    InterferenceContext,
)
from readability_data.java_degradation.interferences.core.java import validate_java
from readability_data.java_degradation.interferences.data_flow import (
    IntroduceNumericIntermediates,
)
from readability_data.java_degradation.interferences.expressions.literals import (
    EncodeIntegerLiterals,
)
from readability_data.java_degradation.registry import interference_registry


class LiteralExpressionPluginTest(unittest.TestCase):
    def test_catalog_replaces_boolean_encoding_with_numeric_intermediates(self) -> None:
        registry = interference_registry()
        self.assertIn("encode-integer-literals", registry)
        self.assertIn("introduce-numeric-intermediates", registry)
        self.assertNotIn("encode-boolean-literals", registry)

    def test_decimal_integers_become_hex_and_booleans_remain_unchanged(self) -> None:
        source = b"""class Values {
  int zero() { return 0; }
  int number() { return 37; }
  long large() { return 1_000_000L; }
  boolean enabled() { return true; }
}
"""
        result = EncodeIntegerLiterals().apply(
            source, InterferenceContext(17, "values")
        )
        validate_java(result.content, "values", "hexadecimal-integers")
        self.assertIn(b"return 0x0;", result.content)
        self.assertIn(b"return 0x25;", result.content)
        self.assertIn(b"return 0xf4240L;", result.content)
        self.assertIn(b"return true;", result.content)
        self.assertEqual(
            result.stats["decimal_integer_literals_rewritten_as_hexadecimal"], 3
        )

    def test_numeric_literals_split_into_two_collision_safe_locals(self) -> None:
        source = b"""class Values {
  int number(int a) {
    return 37 + 8 + 0;
  }
  long large() {
    return 99L;
  }
}
"""
        result = IntroduceNumericIntermediates().apply(
            source, InterferenceContext(17, "values")
        )
        validate_java(result.content, "values", "numeric-intermediates")
        self.assertEqual(result.stats["integer_literals_split"], 4)
        self.assertEqual(result.stats["intermediate_variables_introduced"], 8)
        self.assertIn(b"final int b = 18;", result.content)
        self.assertIn(b"final int c = 19;", result.content)
        self.assertIn(b"(b + c)", result.content)
        self.assertIn(b"1", result.content)
        self.assertIn(b"-1", result.content)
        self.assertNotIn(b"final int a =", result.content)

    def test_explicit_constructor_invocation_is_not_split(self) -> None:
        source = b"""class Values {
  Values() { this(37); }
  Values(int value) {}
}
"""
        result = IntroduceNumericIntermediates().apply(
            source, InterferenceContext(17, "constructor")
        )
        self.assertEqual(result.content, source)
        self.assertEqual(result.stats["integer_literals_split"], 0)

    @unittest.skipUnless(shutil.which("javac"), "JDK is not installed")
    def test_hex_and_numeric_intermediate_outputs_compile(self) -> None:
        sources = {
            "HexValues.java": b"""@interface Flag { int count(); }
@Flag(count = 37)
class HexValues {
  byte smallValue = 3;
  long longValue = 999L;
  int select(int input) {
    switch (input) { case 37: return 3; default: return 999; }
  }
}
""",
            "SplitValues.java": b"""class SplitValues {
  int calculate() { return 37 + 8; }
  long calculateLong() { return 999L; }
}
""",
        }
        transformed = {
            "HexValues.java": EncodeIntegerLiterals()
            .apply(sources["HexValues.java"], InterferenceContext(17, "hex"))
            .content,
            "SplitValues.java": IntroduceNumericIntermediates()
            .apply(sources["SplitValues.java"], InterferenceContext(17, "split"))
            .content,
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, content in transformed.items():
                (Path(directory) / name).write_bytes(content)
            subprocess.run(
                ["javac", "-encoding", "UTF-8", *transformed],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )


if __name__ == "__main__":
    unittest.main()
