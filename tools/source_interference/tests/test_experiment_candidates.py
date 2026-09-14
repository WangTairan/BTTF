from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from readability_experiments.behavior_prediction.builder import (
    build_candidate as build_behavior,
)
from readability_experiments.cli import build_parser
from readability_experiments.common.anchors import python_mutation_anchors
from readability_experiments.common.catalog import dataset_fingerprint
from readability_experiments.common.tests_index import find_test_references
from readability_experiments.test_guided_repair.builder import (
    build_candidate as build_repair,
)


class ExperimentCandidateTests(unittest.TestCase):
    def test_experiment_builders_have_separate_contracts(self) -> None:
        common = {"base_sample_id": "base-1"}
        behavior = build_behavior(common)
        self.assertEqual(behavior["experiment"], "behavior-prediction")
        self.assertNotIn("mutation_anchors", behavior)
        self.assertIsNone(build_repair(common, []))
        repair = build_repair(common, [{"mutation_id": "m1"}])
        self.assertEqual(repair["experiment"], "test-guided-repair")
        self.assertEqual(repair["mutation_anchor_count"], 1)

    def test_cli_defaults_keep_experiments_outside_constructed(self) -> None:
        args = build_parser().parse_args([])
        self.assertEqual(args.output, Path("data/experiments"))
        self.assertNotEqual(args.output.parent, Path("data/constructed"))

    def test_python_anchor_ids_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.py"
            path.write_text(
                "class C:\n    def f(self, x):\n        return x + 1 if x > 0 else False\n"
            )
            first = python_mutation_anchors(path, "sample-1")
            second = python_mutation_anchors(path, "sample-1")
            self.assertEqual(first, second)
            self.assertGreaterEqual(len(first), 3)
            ast.parse(path.read_text())

    def test_python_anchors_include_nested_class_methods_not_local_functions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.py"
            path.write_text(
                "class Outer:\n"
                "    def outer(self, x):\n"
                "        def local(y):\n"
                "            return y * 7\n"
                "        return x + 1\n"
                "    class Inner:\n"
                "        def inner(self, x):\n"
                "            return x - 1\n"
            )
            anchors = python_mutation_anchors(path, "sample-2")
            self.assertEqual(
                {row["method_name"] for row in anchors}, {"outer", "inner"}
            )
            self.assertNotIn("*", {row["original_value"] for row in anchors})

    def test_test_reference_index_is_token_based(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "tests" / "test_sample.py").write_text("value = TargetClass()\n")
            refs, count = find_test_references(
                root, "python", {"Target", "TargetClass"}
            )
            self.assertEqual(count, 1)
            self.assertNotIn("Target", refs)
            self.assertEqual(refs["TargetClass"], ["tests/test_sample.py"])

    def test_dataset_fingerprint_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.jsonl"
            path.write_text(json.dumps({"a": 1}) + "\n")
            first = dataset_fingerprint(root)
            path.write_text(json.dumps({"a": 2}) + "\n")
            self.assertNotEqual(first, dataset_fingerprint(root))


if __name__ == "__main__":
    unittest.main()
