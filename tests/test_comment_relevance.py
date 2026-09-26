import unittest

import numpy as np

from src.methods.readability_model.comment_relevance import select_balanced_threshold
from src.methods.readability_model.embedding_features import (
    _comment_code_relevance_features,
)


class CommentRelevanceTest(unittest.TestCase):
    def test_balanced_threshold_separates_calibration_scores(self) -> None:
        labels = np.asarray([0, 0, 1, 1])
        scores = np.asarray([0.1, 0.2, 0.8, 0.9])
        threshold, balanced_accuracy = select_balanced_threshold(labels, scores)
        self.assertGreater(threshold, 0.2)
        self.assertLess(threshold, 0.8)
        self.assertEqual(balanced_accuracy, 1.0)

    def test_comment_features_use_calibrated_threshold(self) -> None:
        rows = [
            ("COMMENT", "comment_related", 1, np.asarray([1.0, 0.0])),
            ("COMMENT", "comment_unrelated", 1, np.asarray([0.0, 1.0])),
            ("IDENTIFIER", "value", 2, np.asarray([1.0, 0.0])),
        ]
        features = _comment_code_relevance_features(rows, threshold=0.5)
        self.assertAlmostEqual(features["comment_code_similarity_mean"], 0.5)
        self.assertAlmostEqual(features["comment_code_similarity_min"], 0.0)
        self.assertAlmostEqual(features["irrelevant_comment_ratio"], 0.5)
        self.assertAlmostEqual(features["irrelevant_comment_deficit_mean"], 0.25)

    def test_no_comments_are_neutral(self) -> None:
        rows = [("IDENTIFIER", "value", 1, np.asarray([1.0, 0.0]))]
        features = _comment_code_relevance_features(rows, threshold=0.42)
        self.assertEqual(features["comment_code_similarity_mean"], 0.42)
        self.assertEqual(features["comment_code_similarity_min"], 0.42)
        self.assertEqual(features["irrelevant_comment_ratio"], 0.0)
        self.assertEqual(features["irrelevant_comment_deficit_mean"], 0.0)


if __name__ == "__main__":
    unittest.main()
