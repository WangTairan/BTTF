from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readability_experiments.results import RunStore


class ResultStoreTests(unittest.TestCase):
    def test_summary_preserves_unevaluated_and_reasoning_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore.create(
                Path(directory),
                "sample",
                [{"task_id": "t1", "prompt": "p"}],
                {"models": ["m"]},
            )
            store.append(
                {
                    "task_id": "t1",
                    "answer": "answer",
                    "correct": None,
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                        "completion_tokens_details": {"reasoning_tokens": 3},
                    },
                    "raw_response": {
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "message": {
                                    "reasoning_content": "reason",
                                    "content": "answer",
                                },
                            }
                        ],
                    },
                    "response_id": "r1",
                    "model": "m",
                }
            )
            summary = store.finalize()["overall"]
            self.assertEqual(summary["requests"], 1)
            self.assertEqual(summary["unevaluated"], 1)
            self.assertIsNone(summary["accuracy"])
            self.assertEqual(summary["token_totals"]["total_tokens"], 15)
            self.assertEqual(summary["token_totals"]["reasoning_tokens"], 3)
            self.assertEqual(summary["token_totals"]["visible_completion_tokens"], 2)
            self.assertEqual(summary["reasoning"]["total_characters"], 6)
            self.assertTrue((store.directory / "tasks.jsonl").is_file())
            self.assertTrue((store.directory / "run.json").is_file())

    def test_summary_reports_paired_condition_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tasks = [
                {"task_id": "b1-o", "base_task_id": "b1", "condition": "original"},
                {"task_id": "b1-t", "base_task_id": "b1", "condition": "rename"},
                {"task_id": "b2-o", "base_task_id": "b2", "condition": "original"},
                {"task_id": "b2-t", "base_task_id": "b2", "condition": "rename"},
            ]
            store = RunStore.create(Path(directory), "paired", tasks, {})
            for task_id, correct in (
                ("b1-o", True),
                ("b1-t", False),
                ("b2-o", False),
                ("b2-t", True),
            ):
                store.append(
                    {
                        "task_id": task_id,
                        "answer": "",
                        "correct": correct,
                        "usage": {},
                        "raw_response": {"choices": []},
                        "response_id": task_id,
                        "model": "m",
                    }
                )
            summary = store.finalize()
            paired = summary["paired_outcomes"]["by_condition"]["rename"]
            self.assertEqual(paired["pairs"], 2)
            self.assertEqual(paired["degraded"], 1)
            self.assertEqual(paired["improved"], 1)
            self.assertEqual(paired["conditional_degradation_rate"], 1.0)
            self.assertEqual(summary["by_condition"]["original"]["requests"], 2)


if __name__ == "__main__":
    unittest.main()
