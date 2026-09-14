from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

OFFICIAL_BASE_URL = "https://api.groq.com/openai/v1"
BATCH_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
)
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_REASONING_EFFORT = "high"
# The model supports 65,536 tokens, but Groq's batch tier currently enforces
# a 50,000 output-tokens-per-minute ceiling per request for this model.
DEFAULT_MAX_COMPLETION_TOKENS = 50_000
DEFAULT_TEMPERATURE = 1.0


class GroqAPIError(RuntimeError):
    """An error returned by the official Groq API."""


class GroqBatchClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OFFICIAL_BASE_URL,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            raise ValueError("GROQ_API_KEY is not set")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        content_type: str = "application/json",
    ) -> bytes:
        request = urllib.request.Request(
            f"{self._base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
                "Content-Type": content_type,
                "User-Agent": "readability-experiments/0.1",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self._timeout_seconds
            ) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:4000]
            raise GroqAPIError(f"Groq HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise GroqAPIError(f"Groq connection failed: {error.reason}") from error

    def _json_request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8") if payload is not None else None
        try:
            return json.loads(self._request(method, path, body=encoded).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise GroqAPIError("Groq returned invalid JSON") from error

    def upload_batch_file(self, path: Path) -> dict[str, Any]:
        boundary = f"----readability-{uuid.uuid4().hex}"
        pieces = [
            f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'.encode(),
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                f'filename="{path.name}"\r\nContent-Type: application/jsonl\r\n\r\n'
            ).encode(),
            path.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        raw = self._request(
            "POST",
            "/files",
            body=b"".join(pieces),
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise GroqAPIError("Groq returned invalid upload JSON") from error

    def create_batch(
        self, input_file_id: str, completion_window: str
    ) -> dict[str, Any]:
        return self._json_request(
            "POST",
            "/batches",
            {
                "input_file_id": input_file_id,
                "endpoint": "/v1/chat/completions",
                "completion_window": completion_window,
            },
        )

    def retrieve_batch(self, batch_id: str) -> dict[str, Any]:
        return self._json_request("GET", f"/batches/{batch_id}")

    def download_file(self, file_id: str) -> bytes:
        return self._request("GET", f"/files/{file_id}/content")


def batch_request(
    *,
    custom_id: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict[str, Any]:
    if model not in BATCH_MODELS:
        raise ValueError(f"unsupported Groq batch model: {model}")
    if reasoning_effort not in {"low", "medium", "high"}:
        raise ValueError("reasoning_effort must be 'low', 'medium', or 'high'")
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": reasoning_effort,
            "include_reasoning": True,
            "stream": False,
        },
    }
