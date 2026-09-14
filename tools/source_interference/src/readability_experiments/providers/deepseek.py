from __future__ import annotations

import http.client
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

OFFICIAL_BASE_URL = "https://api.deepseek.com"
OFFICIAL_MODELS = ("deepseek-v4-pro", "deepseek-v4-flash")
DEFAULT_THINKING = "enabled"
DEFAULT_REASONING_EFFORT = "high"
# The current V4 documentation does not publish a numeric default.  Repair
# prompts need room for both hidden reasoning and the visible patch, so the
# experiment fixes a larger, explicit cap.
DEFAULT_MAX_TOKENS = 30000
DEFAULT_TEMPERATURE = 1.0


class DeepSeekAPIError(RuntimeError):
    """An error returned by the official DeepSeek API."""


class DeepSeekTransientAPIError(DeepSeekAPIError):
    """A retryable transport or server-side DeepSeek API failure."""


@dataclass(frozen=True)
class DeepSeekResponse:
    model: str
    response_id: str | None
    content: str
    reasoning_content: str | None
    finish_reason: str | None
    usage: dict[str, Any]
    system_fingerprint: str | None
    raw_response: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "response_id": self.response_id,
            "content": self.content,
            "reasoning_content": self.reasoning_content,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "system_fingerprint": self.system_fingerprint,
            "raw_response": self.raw_response,
        }


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OFFICIAL_BASE_URL,
        timeout_seconds: float = 180.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self._api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def chat(
        self,
        prompt: str,
        model: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        thinking: str = DEFAULT_THINKING,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        json_output: bool = False,
    ) -> DeepSeekResponse:
        if model not in OFFICIAL_MODELS:
            raise ValueError(f"unsupported official DeepSeek model: {model}")
        if thinking not in {"enabled", "disabled"}:
            raise ValueError("thinking must be 'enabled' or 'disabled'")
        if reasoning_effort not in {"low", "high", "max"}:
            raise ValueError("reasoning_effort must be 'low', 'high', or 'max'")
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "thinking": {"type": thinking},
            "reasoning_effort": reasoning_effort,
            "stream": False,
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "readability-experiments/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self._timeout_seconds
            ) as response:
                raw_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:2000]
            if error.code in {408, 409, 425, 429, 500, 502, 503, 504}:
                raise DeepSeekTransientAPIError(
                    f"DeepSeek transient HTTP {error.code}: {detail}"
                ) from error
            raise DeepSeekAPIError(f"DeepSeek HTTP {error.code}: {detail}") from error
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            TimeoutError,
            ConnectionError,
            OSError,
        ) as error:
            raise DeepSeekTransientAPIError(
                f"DeepSeek connection interrupted: {error}"
            ) from error
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise DeepSeekTransientAPIError(
                "DeepSeek returned a truncated or invalid JSON response"
            ) from error
        try:
            choice = body["choices"][0]
            message = choice["message"]
            return DeepSeekResponse(
                model=str(body.get("model", model)),
                response_id=body.get("id"),
                content=str(message.get("content") or ""),
                reasoning_content=message.get("reasoning_content"),
                finish_reason=choice.get("finish_reason"),
                usage=dict(body.get("usage") or {}),
                system_fingerprint=body.get("system_fingerprint"),
                raw_response=body,
            )
        except (KeyError, IndexError, TypeError) as error:
            raise DeepSeekAPIError(
                "DeepSeek returned an unexpected response schema"
            ) from error
