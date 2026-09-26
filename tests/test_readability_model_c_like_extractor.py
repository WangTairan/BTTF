from __future__ import annotations

import unittest

from src.methods.readability_model.extractors import CLikeLexemeExtractor, extractor_for_language


class CLikeExtractorTests(unittest.TestCase):
    def test_cuda_uses_explicit_c_like_extractor_without_java_wrapping(self) -> None:
        source = "__global__ void add(float *x) { x[threadIdx.x] += 1.0f; }"
        extractor = extractor_for_language("cuda")

        self.assertIsInstance(extractor, CLikeLexemeExtractor)
        chunks, mode = extractor.extract_with_fallback_mode(source)
        self.assertEqual(mode, "c_like_lexical")
        self.assertTrue(any(chunk.type == "CALL" and "add" in chunk.lexeme for chunk in chunks))
        self.assertTrue(any(chunk.type == "ASSIGNMENT" for chunk in chunks))

    def test_c_like_extractor_rejects_empty_source(self) -> None:
        extractor = extractor_for_language("c++")
        with self.assertRaises(SyntaxError):
            extractor.extract("  \n")

    def test_comment_markers_inside_strings_are_not_comments(self) -> None:
        source = (
            'const char *url = "http://example"; '
            'const char *sql = "/* not a comment */"; '
            "int after = 1; // real comment\n"
        )
        chunks = CLikeLexemeExtractor().extract(source)

        comments = [chunk.lexeme for chunk in chunks if chunk.type == "COMMENT"]
        self.assertEqual(comments, ["comment_real_comment"])
        self.assertTrue(any(chunk.lexeme == "after" for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
