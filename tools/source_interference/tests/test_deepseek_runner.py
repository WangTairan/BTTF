from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from readability_experiments.deepseek_cli import (
    _chat_with_length_retry,
    _check_validated_task,
    _requested_model,
    build_parser,
    run_tasks,
)
from readability_experiments.providers.deepseek import (
    DeepSeekClient,
    DeepSeekResponse,
    DeepSeekTransientAPIError,
)
from readability_experiments.results import RunStore


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return json.dumps(
            {
                "id": "response-1",
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 1,
                    "total_tokens": 4,
                },
            }
        ).encode()


class DeepSeekRunnerTests(unittest.TestCase):
    def test_response_deployment_alias_maps_to_requested_model(self) -> None:
        self.assertEqual(
            _requested_model({"model": "deepseek-flash"}),
            "deepseek-flash",
        )
        self.assertEqual(
            _requested_model(
                {
                    "model": "deepseek-flash",
                    "requested_model": "deepseek-flash",
                }
            ),
            "deepseek-flash",
        )

    def test_length_finish_is_retried_once_and_retained(self) -> None:
        responses = [
            DeepSeekResponse(
                "m",
                "r1",
                "partial",
                None,
                "length",
                {"total_tokens": 9},
                None,
                {"id": "r1"},
            ),
            DeepSeekResponse(
                "m",
                "r2",
                "complete",
                None,
                "stop",
                {"total_tokens": 7},
                None,
                {"id": "r2"},
            ),
        ]
        client = Mock()
        client.chat.side_effect = responses
        response, history, transport_history = _chat_with_length_retry(
            client,
            prompt="p",
            model="deepseek-v4-pro",
            max_tokens=51200,
            thinking="enabled",
            reasoning_effort="high",
            length_retries=1,
        )
        self.assertEqual(response.content, "complete")
        self.assertEqual(history[0]["answer"], "partial")
        self.assertEqual(transport_history, [])
        self.assertEqual(client.chat.call_count, 2)

    @patch("readability_experiments.deepseek_cli.time.sleep")
    def test_transient_transport_failure_is_retried(self, sleep) -> None:
        completed = DeepSeekResponse(
            "m", "r1", "complete", None, "stop", {"total_tokens": 7}, None, {"id": "r1"}
        )
        client = Mock()
        client.chat.side_effect = [
            DeepSeekTransientAPIError("connection interrupted"),
            completed,
        ]
        response, length_history, transport_history = _chat_with_length_retry(
            client,
            prompt="p",
            model="deepseek-flash",
            max_tokens=30000,
            thinking="disabled",
            reasoning_effort="low",
            length_retries=1,
            request_retries=2,
            retry_backoff_seconds=0.25,
        )
        self.assertEqual(response.content, "complete")
        self.assertEqual(length_history, [])
        self.assertEqual(len(transport_history), 1)
        self.assertEqual(transport_history[0]["delay_seconds"], 0.25)
        sleep.assert_called_once_with(0.25)

    def test_validated_task_checks_behavior_and_repair_answers(self) -> None:
        behavior = {
            "experiment": "behavior-prediction",
            "expected": {"stdout_lines": ["x"]},
        }
        self.assertTrue(_check_validated_task(behavior, '{"stdout_lines":["x"]}'))
        repair = {
            "experiment": "test-guided-repair",
            "mutation": "invert_dict_equality",
        }
        valid = (
            "--- a/src/requests/structures.py\n+++ b/src/requests/structures.py\n"
            "-        return dict(self.lower_items()) != dict(other_dict.lower_items())\n"
            "+        return dict(self.lower_items()) == dict(other_dict.lower_items())"
        )
        self.assertTrue(_check_validated_task(repair, valid))
        self.assertFalse(
            _check_validated_task(
                repair, valid.replace("+        return", "         return")
            )
        )
        self.assertIsNone(
            _check_validated_task(
                {
                    "expected_kind": "lightweight_patch_validation",
                    "experiment": "lightweight-test-guided-repair",
                },
                "any model response",
            )
        )

    @patch("urllib.request.urlopen", return_value=_Response())
    def test_client_uses_official_chat_endpoint_without_exposing_key(
        self, mocked
    ) -> None:
        response = DeepSeekClient(api_key="secret-test-key").chat(
            "hello", "deepseek-flash"
        )
        self.assertEqual(response.content, "ok")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertNotIn("secret-test-key", request.data.decode())
        payload = json.loads(request.data)
        self.assertEqual(payload["thinking"], {"type": "enabled"})
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertEqual(payload["max_tokens"], 30000)
        self.assertEqual(payload["temperature"], 1.0)

    def test_cli_uses_provider_reasoning_defaults(self) -> None:
        args = build_parser().parse_args(["run", "--input", "tasks.jsonl"])
        self.assertEqual(args.thinking, "enabled")
        self.assertEqual(args.reasoning_effort, "high")
        self.assertEqual(args.max_tokens, 30000)
        self.assertEqual(args.timeout_seconds, 600.0)
        self.assertEqual(args.request_retries, 5)

    def test_runner_rejects_candidate_inventory_without_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidates.jsonl"
            source.write_text(json.dumps({"candidate_id": "c1"}) + "\n")
            args = build_parser().parse_args(
                ["run", "--input", str(source), "--output-root", str(root / "results")]
            )
            with self.assertRaisesRegex(ValueError, "validated task JSONL"):
                run_tasks(args)

    def test_runner_rejects_repair_task_without_dynamic_prevalidation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "tasks.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "task_id": "repair-1",
                        "experiment": "test-guided-repair",
                        "expected_kind": "external_patch_validation",
                        "prompt": "prompt",
                    }
                )
                + "\n"
            )
            args = build_parser().parse_args(
                ["run", "--input", str(source), "--output-root", str(root / "results")]
            )
            with self.assertRaisesRegex(ValueError, "dynamic prevalidation"):
                run_tasks(args)

    def test_runner_resumes_completed_task_model_pairs_without_api_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = {"task_id": "t1", "experiment": "behavior", "prompt": "prompt"}
            source = root / "tasks.jsonl"
            source.write_text(json.dumps(task) + "\n")
            store = RunStore.create(root / "results", "tasks", [task], {})
            store.append(
                {
                    "task_id": "t1",
                    "answer": "answer",
                    "correct": None,
                    "raw_response": {"choices": [{"finish_reason": "stop"}]},
                    "usage": {},
                    "response_id": "r1",
                    # The API returns this deployment name for requests made with
                    # the documented V4.1 Flash identifier.
                    "model": "deepseek-flash",
                }
            )
            args = build_parser().parse_args(
                [
                    "run",
                    "--input",
                    str(source),
                    "--resume-run",
                    str(store.directory),
                    "--models",
                    "deepseek-flash",
                ]
            )
            result = run_tasks(args)
            self.assertEqual(result["written"], 0)
            self.assertEqual(result["skipped_existing"], 1)


if __name__ == "__main__":
    unittest.main()
