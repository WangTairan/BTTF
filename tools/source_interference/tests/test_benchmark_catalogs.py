from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readability_experiments.benchmark_eval.catalog import (
    bugsinpy_records,
    defects4j_records,
)


class BenchmarkCatalogTests(unittest.TestCase):
    def test_bugsinpy_catalog_reads_metadata_tests_and_production_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bug = root / "projects" / "demo" / "bugs" / "7"
            bug.mkdir(parents=True)
            (bug.parents[1] / "project.info").write_text(
                'github_url="https://example.test/demo"\nstatus="OK"\n'
            )
            (bug / "bug.info").write_text(
                'python_version="3.11"\n'
                'buggy_commit_id="abc"\n'
                'fixed_commit_id ="def"\n'
                'test_file="tests/test_demo.py"\n'
            )
            (bug / "bug_patch.txt").write_text(
                "diff --git a/pkg/model.py b/pkg/model.py\n"
                "diff --git a/tests/test_demo.py b/tests/test_demo.py\n"
            )
            (bug / "run_test.sh").write_text(
                "pytest -q tests/test_demo.py::test_case\n"
            )
            records = bugsinpy_records(root, root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["instance_id"], "bugsinpy__demo__7")
            self.assertEqual(records[0]["production_source_paths"], ["pkg/model.py"])
            self.assertTrue(records[0]["single_production_source_file"])

    def test_defects4j_catalog_supports_header_and_metadata_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "framework" / "projects" / "Demo"
            (project / "patches").mkdir(parents=True)
            (project / "modified_classes").mkdir()
            (project / "trigger_tests").mkdir()
            (project / "active-bugs.csv").write_text("bug.id\n1\n2\n")
            (project / "patches" / "1.src.patch").write_text(
                "diff --git a/src/Demo.java b/src/Demo.java\n"
            )
            (project / "modified_classes" / "1.src").write_text("example.Demo\n")
            (project / "trigger_tests" / "1").write_text(
                "--- example.DemoTest::fails\nAssertionError: expected failure\n"
            )
            records = defects4j_records(root, root)
            self.assertEqual([row["bug_id"] for row in records], ["1", "2"])
            self.assertEqual(records[0]["production_source_paths"], ["src/Demo.java"])
            self.assertEqual(records[0]["trigger_tests"], ["example.DemoTest::fails"])
            self.assertIsNone(records[1]["patch_sha256"])


if __name__ == "__main__":
    unittest.main()
