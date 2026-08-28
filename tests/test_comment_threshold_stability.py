import random
import unittest

import numpy as np

from experiments.cognascore.auxiliary.comment_threshold_stability import (
    CommentTask,
    evaluate_repeat,
    stratified_quotas,
)
from experiments.cognascore.auxiliary.comment_constructed_probe import threshold_metrics


class CommentThresholdStabilityTest(unittest.TestCase):
    DATASETS = ("a", "b", "c", "d", "e", "f")

    def test_stratified_quotas_cover_requested_sample(self) -> None:
        quotas = stratified_quotas(50, self.DATASETS, random.Random(42))
        self.assertEqual(sum(quotas.values()), 50)
        self.assertEqual(set(quotas.values()), {8, 9})

    def test_stratified_quotas_redistribute_limited_capacity(self) -> None:
        capacities = {dataset: 20 for dataset in self.DATASETS}
        capacities["f"] = 4
        quotas = stratified_quotas(50, self.DATASETS, random.Random(42), capacities)
        self.assertEqual(sum(quotas.values()), 50)
        self.assertEqual(quotas["f"], 4)
        self.assertTrue(all(quotas[key] <= capacities[key] for key in self.DATASETS))

    def test_mismatched_comments_always_come_from_another_task(self) -> None:
        grouped = {}
        for dataset_index, dataset in enumerate(self.DATASETS):
            grouped[dataset] = []
            for task_index in range(2):
                vector = np.asarray([1.0, float(dataset_index + task_index + 1)])
                grouped[dataset].append(
                    CommentTask(
                        dataset=dataset,
                        task_id=f"{dataset}-{task_index}",
                        code_matrix=np.asarray([vector / np.linalg.norm(vector)]),
                        comments=((f"comment-{dataset}-{task_index}", vector),),
                    )
                )
        first, pairs = evaluate_repeat(grouped, self.DATASETS, 12, 7, 0.5)
        second, repeated_pairs = evaluate_repeat(grouped, self.DATASETS, 12, 7, 0.5)
        self.assertEqual(first, second)
        self.assertEqual(
            [(row["code_task_id"], row["comment_task_id"]) for row in pairs],
            [(row["code_task_id"], row["comment_task_id"]) for row in repeated_pairs],
        )
        mismatched = [row for row in pairs if row["role"] == "mismatched"]
        self.assertEqual(len(mismatched), 12)
        self.assertTrue(
            all(row["code_task_id"] != row["comment_task_id"] for row in mismatched)
        )

    def test_constructed_probe_detects_increased_irrelevance(self) -> None:
        pairs = [
            {
                "original_scores": [0.8, 0.7],
                "injected_scores": [0.8, 0.7, 0.2],
                "new_comment_scores": [0.2],
            }
        ]
        metrics = threshold_metrics(pairs, 0.5)
        self.assertEqual(metrics["strict_pairwise_direction_accuracy"], 1.0)
        self.assertEqual(metrics["new_injected_comment_detection_rate"], 1.0)
        self.assertEqual(metrics["original_comment_retention_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
