from __future__ import annotations

import ast
import unittest

from readability_experiments.pilot import (
    _inject_equality_bug,
    _inject_membership_bug,
    _inject_version_length_bug,
    _replace_class,
)


class ExperimentPilotTests(unittest.TestCase):
    def test_replace_class_preserves_module_context(self) -> None:
        module = (
            "before = 1\n\nclass Target:\n    value = 1\n\nclass Other:\n    pass\n"
        )
        variant = "import ignored\n\nclass Target:\n    value = 2\n"
        actual = _replace_class(module, variant, "Target")
        self.assertIn("before = 1", actual)
        self.assertIn("value = 2", actual)
        self.assertIn("class Other", actual)
        self.assertNotIn("import ignored", actual)
        ast.parse(actual)

    def test_inject_equality_bug_targets_dict_comparison(self) -> None:
        source = (
            "class Target:\n"
            "    def same(self, other):\n"
            "        if other == 3:\n"
            "            return dict(self.items()) == dict(other.items())\n"
        )
        mutant = _inject_equality_bug(source, "Target")
        self.assertIn("other == 3", mutant)
        self.assertIn("dict(self.items()) != dict(other.items())", mutant)
        ast.parse(mutant)

    def test_inject_membership_bug_targets_instance_dictionary(self) -> None:
        source = (
            "class Target:\n"
            "    def get(self, key):\n"
            "        if key in self.__dict__:\n"
            "            return self.__dict__[key]\n"
        )
        mutant = _inject_membership_bug(source, "Target")
        self.assertIn("if key not in self.__dict__:", mutant)
        ast.parse(mutant)

    def test_inject_version_length_bug_targets_parser_guard(self) -> None:
        source = (
            "class VersionInfo:\n"
            "    def parse(self, value):\n"
            "        parts = value.split('.')\n"
            "        if len(parts) == 3:\n"
            "            parts.append('final')\n"
        )
        mutant = _inject_version_length_bug(source, "VersionInfo")
        self.assertIn("if len(parts) != 3:", mutant)
        ast.parse(mutant)


if __name__ == "__main__":
    unittest.main()
