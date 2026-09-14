from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from readability_experiments.groq_cli import (
    _is_complete_response,
    _response_record,
    build_parser,
    submit,
)
from readability_experiments.providers.groq import GroqBatchClient, batch_request


class _Response:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.value).encode()


class GroqBatchRunnerTests(unittest.TestCase):
    def test_batch_request_uses_high_reasoning_and_one_user_message(self) -> None:
        row = batch_request(custom_id="request-1", prompt="repair this")
        self.assertEqual(row["url"], "/v1/chat/completions")
        self.assertEqual(row["body"]["model"], "openai/gpt-oss-120b")
        self.assertEqual(row["body"]["reasoning_effort"], "high")
        self.assertTrue(row["body"]["include_reasoning"])
        self.assertEqual(row["body"]["max_completion_tokens"], 50000)
        self.assertEqual(
            row["body"]["messages"], [{"role": "user", "content": "repair this"}]
        )

    @patch("urllib.request.urlopen", return_value=_Response({"id": "file-1"}))
    def test_upload_uses_official_files_endpoint_without_leaking_key(
        self, mocked
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text("{}\n", encoding="utf-8")
            result = GroqBatchClient(api_key="secret-test-key").upload_batch_file(path)
        self.assertEqual(result["id"], "file-1")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/files")
        self.assertNotIn(b"secret-test-key", request.data)
        self.assertIn(b'name="purpose"', request.data)
        self.assertIn(b"batch", request.data)

    def test_prepare_only_splits_requests_and_records_groq_secret_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "tasks.jsonl"
            tasks = [{"task_id": f"t{i}", "prompt": f"prompt {i}"} for i in range(3)]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in tasks), encoding="utf-8"
            )
            args = build_parser().parse_args(
                [
                    "submit",
                    "--input",
                    str(input_path),
                    "--output-root",
                    str(root / "results"),
                    "--batch-size",
                    "2",
                    "--prepare-only",
                ]
            )
            result = submit(args)
            run = Path(result["run_directory"])
            self.assertEqual(result["batches_prepared"], 2)
            self.assertEqual(len(list((run / "batch-inputs").glob("*.jsonl"))), 2)
            metadata = json.loads((run / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["secret_sources"], ["GROQ_API_KEY"])
            self.assertEqual(metadata["configuration"]["reasoning_effort"], "high")
            self.assertEqual(metadata["configuration"]["completion_window"], "24h")

    def test_batch_output_is_normalized_to_existing_result_schema(self) -> None:
        line = {
            "custom_id": "request-000001",
            "response": {
                "status_code": 200,
                "body": {
                    "id": "chat-1",
                    "model": "openai/gpt-oss-120b",
                    "choices": [
                        {
                            "message": {"content": "answer", "reasoning": "thought"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 4,
                        "completion_tokens": 8,
                        "total_tokens": 12,
                    },
                },
            },
        }
        record = _response_record(
            line, {"request-000001": {"task_id": "t1", "model": "openai/gpt-oss-120b"}}
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["answer"], "answer")
        self.assertEqual(record["inference_status"], "completed")
        self.assertEqual(
            record["raw_response"]["choices"][0]["message"]["reasoning"], "thought"
        )
        self.assertEqual(record["usage"]["total_tokens"], 12)
        self.assertTrue(_is_complete_response(record))

    def test_length_response_with_empty_answer_is_not_complete(self) -> None:
        record = {
            "answer": "",
            "raw_response": {
                "choices": [{"finish_reason": "length", "message": {"content": ""}}]
            },
        }
        self.assertFalse(_is_complete_response(record))


if __name__ == "__main__":
    unittest.main()
