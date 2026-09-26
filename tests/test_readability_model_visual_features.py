from __future__ import annotations

import unittest

from src.methods.readability_model.extractors.java import LexemeExtractor
from src.methods.readability_model.extractors.python_ast import PythonAstLexemeExtractor
from src.methods.readability_model.visual_features import visual_layout_features


class ReadabilityModelVisualFeatureTests(unittest.TestCase):
    def test_python_comments_are_ignored_and_floor_division_is_an_operator(self) -> None:
        source = (
            "value = total // count  # == fake comparison\n"
            "if value is None:\n"
            "    return value\n"
        )
        chunks = PythonAstLexemeExtractor().extract(source)
        features = visual_layout_features(source, chunks, language="python")

        self.assertAlmostEqual(features["operator_density"], 4.0 / 3.0)
        self.assertAlmostEqual(features["decision_density"], 1.0 / 3.0)

    def test_java_comment_markers_inside_strings_are_not_extracted(self) -> None:
        source = (
            'class A { void f() { String url = "http://example"; '
            'String sql = "/* not a comment */"; int after = 1; '
            "// real comment\n} }"
        )
        chunks, mode = LexemeExtractor().extract_with_fallback_mode(source)

        self.assertEqual(mode, "direct_ast")
        comments = [chunk.lexeme for chunk in chunks if chunk.type == "COMMENT"]
        self.assertEqual(comments, ["comment_real_comment"])
        self.assertTrue(any(chunk.lexeme == "after" for chunk in chunks))

    def test_character_density_really_excludes_internal_whitespace(self) -> None:
        features = visual_layout_features("left = right", [], language="java")
        self.assertAlmostEqual(features["operator_character_share"], 1.0 / 10.0)

    def test_java_word_comparison_is_counted_as_an_operator_and_comparison(self) -> None:
        features = visual_layout_features(
            "value instanceof String",
            [],
            language="java",
        )
        self.assertEqual(features["operator_density"], 1.0)
        self.assertEqual(features["decision_density"], 1.0)

    def test_unknown_visual_feature_language_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported visual-feature language"):
            visual_layout_features("x = 1", [], language="unknown")


if __name__ == "__main__":
    unittest.main()
