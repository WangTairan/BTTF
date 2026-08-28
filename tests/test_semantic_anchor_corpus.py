from __future__ import annotations

import unittest
from collections import Counter

from experiments.cognascore.auxiliary.materialize_semantic_anchor_corpus import (
    ALGORITHM_VERSION,
    SAMPLES_PER_SOURCE,
    verify,
)


class SemanticAnchorCorpusTest(unittest.TestCase):
    def test_frozen_manifest_and_snippet_hashes(self) -> None:
        manifest = verify()
        self.assertEqual(manifest["algorithm_version"], ALGORITHM_VERSION)
        self.assertEqual(len(manifest["sources"]), 4)
        self.assertEqual(len(manifest["samples"]), 4 * SAMPLES_PER_SOURCE)

    def test_corpus_is_balanced_by_category_and_language(self) -> None:
        manifest = verify()
        counts = Counter(
            (row["category"], row["language"]) for row in manifest["samples"]
        )
        self.assertEqual(
            counts,
            {
                ("mathematical", "python"): 12,
                ("mathematical", "java"): 12,
                ("application", "python"): 12,
                ("application", "java"): 12,
            },
        )

    def test_readability_benchmarks_are_not_anchor_sources(self) -> None:
        manifest = verify()
        repositories = {row["repository"] for row in manifest["sources"]}
        self.assertEqual(
            repositories,
            {
                "https://github.com/sympy/sympy",
                "https://github.com/apache/commons-math",
                "https://github.com/django/django",
                "https://github.com/spring-projects/spring-petclinic",
            },
        )
        self.assertEqual(manifest["benchmark_overlap"], "none; no readability benchmark supplies anchors")


if __name__ == "__main__":
    unittest.main()
