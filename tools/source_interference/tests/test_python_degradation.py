from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from readability_data.python_degradation import construct_python_dataset
from readability_data.python_degradation.core import Context
from readability_data.python_degradation.registry import INTERFERENCES

SOURCE = '''import math

class Example:
    """Readable example."""

    def calculate_total(self, item_count=2):
        # Explain the useful operation.
        running_total = item_count + 3
        if running_total > 4:
            return True
        else:
            return False
'''


class PythonDegradationTests(unittest.TestCase):
    def test_catalog_matches_java_comparative_design(self):
        self.assertEqual(len(INTERFERENCES), 13)
        self.assertEqual(
            {plugin.category for plugin in INTERFERENCES.values()},
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

    def test_every_plugin_is_deterministic_and_parseable(self):
        context = Context(20260823, "example")
        for slug, plugin in INTERFERENCES.items():
            with self.subTest(slug=slug):
                first = plugin.apply(SOURCE, context)
                second = plugin.apply(SOURCE, context)
                self.assertEqual(first, second)
                ast.parse(first.source)

    def test_identifier_renaming_does_not_rename_imports(self):
        source = """import value
class Example:
    def method(self):
        value = 1
        return value
"""
        result = INTERFERENCES["garble-identifiers"].apply(source, Context(1, "scope"))
        self.assertIn("import value", result.source)
        ast.parse(result.source)

    def test_condition_inversion_preserves_branch_comments(self):
        source = """class Example:
    def choose(self, enabled):
        if enabled:
            # Keep the true-branch explanation.
            return 1
        else:
            # Keep the false-branch explanation.
            return 2
"""
        result = INTERFERENCES["invert-conditions"].apply(
            source, Context(1, "comments")
        )
        self.assertIn("# Keep the true-branch explanation.", result.source)
        self.assertIn("# Keep the false-branch explanation.", result.source)
        self.assertIn("if not (enabled):", result.source)
        ast.parse(result.source)

    def test_end_to_end_balanced_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repositories = {}
            for project in ("django", "flask", "requests", "attrs"):
                repository = root / project
                repository.mkdir()
                (repository / "module.py").write_text(SOURCE, encoding="utf-8")
                repositories[project] = repository
            output = root / "constructed"
            with patch(
                "readability_data.python_degradation.sampling._commit",
                return_value="a" * 40,
            ):
                provenance = construct_python_dataset(
                    repositories, output, per_project=1, seed=7
                )
            rows = [
                json.loads(line)
                for line in (output / "manifest.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(provenance["base_class_count"], 4)
            self.assertEqual(len(rows), 56)
            self.assertEqual(len(list(output.rglob("*.py"))), 56)
            self.assertTrue((output / "obfuscation-report.html").is_file())


if __name__ == "__main__":
    unittest.main()
