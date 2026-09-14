import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from readability_data.java_degradation.engine import JavaInterferenceEngine
from readability_data.java_degradation.interferences.code_injection.low_readability import (
    InjectLowReadabilityCode,
)
from readability_data.java_degradation.interferences.code_injection.low_readability_templates import (
    LOW_READABILITY_TEMPLATES,
)
from readability_data.java_degradation.interferences.code_injection.readable import (
    InjectReadableCode,
)
from readability_data.java_degradation.interferences.code_injection.readable_templates import (
    READABLE_TEMPLATES,
)
from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
)
from readability_data.java_degradation.interferences.core.java import validate_java
from readability_data.java_degradation.interferences.identifiers.meaningful_names import (
    LOCAL_MEANINGFUL_NAMES,
    METHOD_MEANINGFUL_NAMES,
    ranked_misleading_names,
)
from readability_data.java_degradation.interferences.identifiers.rename import (
    RenameIdentifiers,
    _proguard_style_name,
)
from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG,
    interference_registry,
)

SOURCE = b"""/** documentation */
class Example {
  int calculateTotal(int itemCount) {
    if (true) {
      return itemCount + 12;
    }
    return 0;
  }
}
"""


class InterferencePluginTest(unittest.TestCase):
    def test_proguard_style_names_use_shortest_mixed_case_sequence(self) -> None:
        self.assertEqual(
            [
                _proguard_style_name(index)
                for index in (0, 25, 26, 51, 52, 53, 103, 104)
            ],
            ["a", "z", "A", "Z", "aa", "ab", "aZ", "ba"],
        )

    def test_registry_contains_unique_interface_implementations(self) -> None:
        registry = interference_registry()

        self.assertEqual(len(registry), len(INTERFERENCE_CATALOG))
        self.assertEqual(len(registry), 13)
        self.assertTrue(
            all(isinstance(plugin, Interference) for plugin in INTERFERENCE_CATALOG)
        )
        self.assertEqual(
            {plugin.category for plugin in INTERFERENCE_CATALOG},
            {
                "comments",
                "identifiers",
                "expressions",
                "data-flow",
                "code-injection",
                "layout",
                "control-flow",
            },
        )
        self.assertNotIn("fragment-strings", registry)

    def test_readable_and_low_readability_injections_are_isolated(self) -> None:
        source = b"""class Child extends Parent {
  Child() { super(1); }
}
"""
        degrader = JavaInterferenceEngine(17)
        readable = degrader.apply_interferences(
            source, "constructors", ["inject-readable-unrelated-code"]
        )
        unreadable = degrader.apply_interferences(
            source, "constructors", ["inject-low-readability-unrelated-code"]
        )

        readable_match = re.search(
            rb"(runningTotal|remainingSteps|evenNumberCount|firstScore|"
            rb"morningTemperature|totalScore|factorial|featureEnabled|"
            rb"previousNumber|startingPosition)(?:[2-9][0-9]*)?",
            readable.content,
        )
        unreadable_match = re.search(rb"lI0O_[0-9a-f]{8}", unreadable.content)
        self.assertIsNotNone(readable_match)
        self.assertIsNotNone(unreadable_match)
        self.assertEqual(
            readable.stats["inject-readable-unrelated-code_readable_blocks_injected"],
            1,
        )
        self.assertEqual(
            unreadable.stats[
                "inject-low-readability-unrelated-code_low_readability_blocks_injected"
            ],
            1,
        )
        self.assertLess(
            readable.content.index(b"super(1);"),
            readable_match.start(),
        )
        self.assertLess(
            unreadable.content.index(b"super(1);"),
            unreadable_match.start(),
        )

    def test_code_injection_has_ten_templates_per_readability_class(self) -> None:
        self.assertEqual(len(READABLE_TEMPLATES), 10)
        self.assertEqual(len(LOW_READABILITY_TEMPLATES), 10)

        selected_readable = {
            JavaInterferenceEngine(seed)
            .apply_interferences(SOURCE, "example", ["inject-readable-unrelated-code"])
            .stats["inject-readable-unrelated-code_readable_template_index"]
            for seed in range(30)
        }
        selected_low = {
            JavaInterferenceEngine(seed)
            .apply_interferences(
                SOURCE, "example", ["inject-low-readability-unrelated-code"]
            )
            .stats[
                "inject-low-readability-unrelated-code_low_readability_template_index"
            ]
            for seed in range(30)
        }
        self.assertGreater(len(selected_readable), 1)
        self.assertGreater(len(selected_low), 1)

    def test_readable_template_uses_numeric_suffix_only_for_real_collisions(
        self,
    ) -> None:
        source = b"""class Names {
  int run(int runningTotal, int currentNumber) { return runningTotal; }
}
"""
        result = InjectReadableCode(template_index=0).apply(
            source, InterferenceContext(17, "names")
        )
        validate_java(result.content, "names", "readable-template-0")

        self.assertIn(b"runningTotal2", result.content)
        self.assertIn(b"currentNumber2", result.content)
        self.assertNotRegex(result.content, rb"(runningTotal|currentNumber)_[0-9a-f]+")

    def test_misleading_names_are_meaningful_deterministic_and_consistent(self) -> None:
        degrader = JavaInterferenceEngine(17)
        first = degrader.apply_interferences(SOURCE, "example", ["mislead-identifiers"])
        second = degrader.apply_interferences(
            SOURCE, "example", ["mislead-identifiers"]
        )

        self.assertEqual(first, second)
        self.assertNotIn(b"calculateTotal", first.content)
        self.assertNotIn(b"itemCount", first.content)
        method_match = re.search(rb"int ([A-Za-z_$][\w$]*)\(", first.content)
        self.assertIsNotNone(method_match)
        self.assertIn(method_match.group(1).decode(), METHOD_MEANINGFUL_NAMES)
        self.assertEqual(
            first.stats["mislead-identifiers_local_alphabetic_fallbacks_used"], 0
        )
        self.assertEqual(
            first.stats["mislead-identifiers_method_alphabetic_fallbacks_used"], 0
        )

    def test_protected_java_method_name_is_not_renamed(self) -> None:
        source = (
            b"class Solution { int publicApi(int itemCount) { return itemCount; } }"
        )
        for mode in ("short", "misleading", "garbled"):
            result = RenameIdentifiers(mode).apply(
                source,
                InterferenceContext(17, mode, protected_names=("publicApi",)),
            )
            self.assertIn(b"publicApi(", result.content)
            self.assertNotIn(b"itemCount", result.content)

    def test_misleading_name_pools_are_compact_and_length_first(self) -> None:
        self.assertIn(len(LOCAL_MEANINGFUL_NAMES), range(450, 551))
        self.assertIn(len(METHOD_MEANINGFUL_NAMES), range(450, 551))
        self.assertLessEqual(max(map(len, LOCAL_MEANINGFUL_NAMES)), 16)
        self.assertLessEqual(max(map(len, METHOD_MEANINGFUL_NAMES)), 18)
        self.assertTrue(
            all(
                not any(character.isdigit() for character in name)
                for name in (*LOCAL_MEANINGFUL_NAMES, *METHOD_MEANINGFUL_NAMES)
            )
        )
        context = InterferenceContext(17, "lengths")
        for length in range(3, 15):
            ranked = ranked_misleading_names("x" * length, context, 19, method=False)
            self.assertEqual(len(ranked[0]), length)
        for length in range(3, 16):
            ranked = ranked_misleading_names("x" * length, context, 19, method=True)
            self.assertEqual(len(ranked[0]), length)
        self.assertEqual(
            len(ranked_misleading_names("x" * 30, context, 19, method=False)[0]),
            14,
        )
        equal_length_choices = {
            ranked_misleading_names(
                "originalX",
                InterferenceContext(17, f"sample-{index}"),
                19,
                method=False,
            )[0]
            for index in range(20)
        }
        self.assertGreater(len(equal_length_choices), 5)
        self.assertTrue(
            all(len(name) == len("originalX") for name in equal_length_choices)
        )

    def test_misleading_names_exhaust_random_pool_before_fallback(self) -> None:
        available = "tempValue"
        occupied = [name for name in LOCAL_MEANINGFUL_NAMES if name != available]
        fields = "\n".join(f"  int {name};" for name in occupied)
        source = f"""class Collision {{
{fields}
  int execute(int originalX) {{ return originalX; }}
}}
""".encode()
        result = JavaInterferenceEngine(17).apply_interferences(
            source, "collision", ["mislead-identifiers"]
        )

        self.assertGreater(
            result.stats["mislead-identifiers_local_collision_candidates_skipped"],
            0,
        )
        self.assertEqual(
            result.stats["mislead-identifiers_local_alphabetic_fallbacks_used"], 0
        )
        parameter = re.search(rb"\(int ([A-Za-z_$][\w$]*)\)", result.content)
        self.assertIsNotNone(parameter)
        self.assertEqual(parameter.group(1).decode(), available)
        self.assertNotRegex(parameter.group(1), rb"\d")

    def test_misleading_name_fallback_uses_letters_not_digits(self) -> None:
        fields = "\n".join(f"  int {name};" for name in LOCAL_MEANINGFUL_NAMES)
        source = f"""class Exhausted {{
{fields}
  int execute(int originalX) {{ return originalX; }}
}}
""".encode()
        result = JavaInterferenceEngine(17).apply_interferences(
            source, "fallback", ["mislead-identifiers"]
        )
        parameter = re.search(rb"\(int ([A-Za-z_$][\w$]*)\)", result.content)
        self.assertIsNotNone(parameter)
        self.assertRegex(parameter.group(1), rb"^value[A-Z]+$")
        self.assertEqual(
            result.stats["mislead-identifiers_local_alphabetic_fallbacks_used"],
            1,
        )

    @unittest.skipUnless(shutil.which("javac"), "javac is not installed")
    def test_new_interferences_compile_together(self) -> None:
        source = b"""public class Compilable {
  Compilable() { /* explicit invocation must remain first */ this(1); }
  Compilable(int initialValue) {}
  int calculateTotal(int itemCount) {
    int resultValue = itemCount + 3;
    return resultValue;
  }
}
"""
        result = JavaInterferenceEngine(17).apply_interferences(
            source,
            "compilable",
            [
                "insert-dead-branches",
                "inject-readable-unrelated-code",
                "inject-low-readability-unrelated-code",
                "mislead-identifiers",
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Compilable.java"
            path.write_bytes(result.content)
            subprocess.run(
                ["javac", "-encoding", "UTF-8", path.name],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )

    @unittest.skipUnless(shutil.which("javac"), "javac is not installed")
    def test_all_twenty_code_templates_compile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for label, plugin_type in (
                ("Readable", InjectReadableCode),
                ("Opaque", InjectLowReadabilityCode),
            ):
                for index in range(10):
                    class_name = f"{label}Template{index}"
                    source = (
                        f"public class {class_name} {{\n"
                        "  public int run() { return 1; }\n"
                        "}\n"
                    ).encode()
                    result = plugin_type(template_index=index).apply(
                        source, InterferenceContext(17, class_name)
                    )
                    validate_java(result.content, class_name, f"template-{index}")
                    path = Path(directory) / f"{class_name}.java"
                    path.write_bytes(result.content)
                    paths.append(path.name)
            subprocess.run(
                ["javac", "-encoding", "UTF-8", *paths],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )

    def test_layout_plugin_preserves_line_comment_boundaries(self) -> None:
        source = b"""class Comments {
  // This line must keep its terminating newline.
  int value() {
    return 12;
  }
}
"""
        variant = JavaInterferenceEngine(17).apply_interferences(
            source, "comments", ["partially-compact-layout"]
        )

        self.assertIn(
            b"// This line must keep its terminating newline.\n", variant.content
        )


if __name__ == "__main__":
    unittest.main()
