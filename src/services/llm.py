import json
import hashlib
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from openai import OpenAI
from groq import Groq
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential


MODELS = {
    "gpt61-sol": {
        "id": "gpt-6.1-sol",
        "provider": "openai",
    },
    "gpt6-sol": {
        "id": "gpt-6-sol",
        "provider": "openai",
    },
    "gpt5-nano": {
        "id": "gpt-5-nano-2025-08-07",
        "provider": "openai",
    },
    "gpt5-mini": {
        "id": "gpt-5-mini",
        "provider": "openai",
    },
    "gpt54-mini": {
        "id": "gpt-5.4-mini",
        "provider": "openai",
    },
    "gpt-oss": {
        "id": "openai/gpt-oss-120b",
        "provider": "groq",
    },
    "qwen3-32b": {
        "id": "qwen/qwen3-32b",
        "provider": "groq",
    },
    "qwen35p": {
        "id": "qwen/qwen3.5-plus-02-15",
        "provider": "openrouter",
    },
    "ds-v32": {
        "id": "deepseek/deepseek-v3.2",
        "provider": "openrouter",
    },
    "dsv4-pro": {
        "id": "deepseek-v4-pro",
        "provider": "deepseek",
    },
    "llama3-70": {
        "id": "llama-3.3-70b-versatile",
        "provider": "groq",
    },
    "gemma": {
        "id": "google/gemma-4-26b-a4b-it:free",
        "provider": "openrouter",
    },
}


def supports_batch_api(model_name: str) -> bool:
    """Return whether the configured provider supports our remote batch path."""
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    info = MODELS[model_name]
    return info["provider"] in ("openai", "groq") and info.get("batch_api", True)


_openai_client = None
_groq_client = None
_openrouter_client = None
_deepseek_client = None


class MissingAPIKeyError(RuntimeError):
    pass


@dataclass(frozen=True)
class BatchChatFailure:
    index: int
    custom_id: str
    error: Any


class BatchChatError(RuntimeError):
    def __init__(self, message: str, failures: Sequence[BatchChatFailure]):
        super().__init__(message)
        self.failures = tuple(failures)


BatchProgressFn = Callable[[str, int, int], None]


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("OPENAI_API_KEY not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("GROQ_API_KEY not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _get_openrouter_client():
    global _openrouter_client
    if _openrouter_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("OPENROUTER_API_KEY not set")

        referer = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
        title = os.getenv("OPENROUTER_APP_NAME", "my-app")

        _openrouter_client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": referer,
                "X-OpenRouter-Title": title,
            },
        )
    return _openrouter_client


def _get_deepseek_client():
    global _deepseek_client
    if _deepseek_client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("DEEPSEEK_API_KEY not set")
        _deepseek_client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
    return _deepseek_client


def _get_client(provider: str):
    if provider == "openai":
        return _get_openai_client()
    if provider == "groq":
        return _get_groq_client()
    if provider == "openrouter":
        return _get_openrouter_client()
    if provider == "deepseek":
        return _get_deepseek_client()
    raise ValueError(f"Unknown provider: {provider}")


def _obj_get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _apply_reasoning_controls(
    provider: str,
    model_name: str,
    model_id: str,
    body: dict[str, Any],
) -> None:
    if provider == "groq" and model_name == "qwen3-32b":
        body["reasoning_effort"] = "none"
        body["include_reasoning"] = False

    if provider == "groq" and model_name == "gpt-oss":
        body["reasoning_effort"] = "medium"
        body["include_reasoning"] = True
        body["max_completion_tokens"] = 8192

    if provider == "openai" and model_name in {"gpt5-nano", "gpt5-mini"}:
        body["reasoning_effort"] = "minimal"

    if provider == "openai" and model_name == "gpt6-sol":
        body["reasoning_effort"] = "none"

    if provider == "openai" and model_name == "gpt61-sol":
        body.pop("temperature", None)
        body["reasoning_effort"] = "low"
        body["max_completion_tokens"] = 2048

    if provider == "deepseek" and model_name == "dsv4-pro":
        body["extra_body"] = {"thinking": {"type": "disabled"}}


def _build_chat_body(
    model_name: str,
    messages: Sequence[dict[str, Any]],
    **kwargs: Any,
) -> tuple[str, str, dict[str, Any]]:
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    info = MODELS[model_name]
    model_id = info["id"]
    provider = info["provider"]
    body = {
        "model": model_id,
        "messages": _provider_messages(provider, messages),
    }
    temperature = kwargs.pop("temperature", 1)
    if provider != "deepseek":
        body["temperature"] = temperature
    body.update(kwargs)
    _apply_reasoning_controls(provider, model_name, model_id, body)
    return provider, model_id, body


def _provider_messages(
    provider: str,
    messages: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    if provider != "deepseek":
        return list(messages)
    return [
        {**message, "role": "system"}
        if message.get("role") == "developer"
        else dict(message)
        for message in messages
    ]


def _message_content(response_body: Any) -> str:
    choices = _obj_get(response_body, "choices", ())
    first_choice = choices[0]
    message = _obj_get(first_choice, "message")

    content = _obj_get(message, "content", "")
    if content is None:
        content = ""
    if not isinstance(content, str):
        content = str(content)

    reasoning = _obj_get(message, "reasoning", "")
    if reasoning is None:
        reasoning = ""
    if not isinstance(reasoning, str):
        reasoning = str(reasoning)

    content = content.strip()
    reasoning = reasoning.strip()
    if reasoning:
        content = f"<reasoning>\n{reasoning}\n</reasoning>\n\n{content}".strip()

    return content


def chat(model_name: str, prompt: str, **kwargs: Any) -> str:
    return chat_messages(
        model_name,
        [{"role": "user", "content": prompt}],
        **kwargs,
    )


def chat_with_metadata(model_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Return response text together with the complete serializable API response."""
    return chat_messages_with_metadata(
        model_name,
        [{"role": "user", "content": prompt}],
        **kwargs,
    )


def chat_messages(
    model_name: str,
    messages: Sequence[dict[str, Any]],
    **kwargs: Any,
) -> str:
    return str(chat_messages_with_metadata(model_name, messages, **kwargs)["content"])


@retry(
    retry=retry_if_not_exception_type(MissingAPIKeyError),
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=5, min=1, max=90),
)
def chat_messages_with_metadata(
    model_name: str,
    messages: Sequence[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    provider, requested_model, body = _build_chat_body(
        model_name,
        messages,
        **kwargs,
    )
    client = _get_client(provider)
    response = client.chat.completions.create(**body)
    return _chat_response_record(
        response,
        provider=provider,
        configured_model=model_name,
        requested_model=requested_model,
        request_parameters={key: value for key, value in body.items() if key != "messages"},
    )


def _chat_response_record(
    response: Any,
    *,
    provider: str,
    configured_model: str,
    requested_model: str,
    request_parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "content": _message_content(response),
        "provider": provider,
        "configured_model": configured_model,
        "requested_model": requested_model,
        "response_id": _obj_get(response, "id"),
        "response_model": _obj_get(response, "model"),
        "created": _obj_get(response, "created"),
        "finish_reason": _first_finish_reason(response),
        "usage": _serializable_value(_obj_get(response, "usage")),
        "request_parameters": _serializable_value(
            request_parameters
        ),
        "api_response": _serializable_value(response),
    }


def _first_finish_reason(response: Any) -> Any:
    choices = _obj_get(response, "choices", ())
    if not choices:
        return _obj_get(response, "status")
    return _obj_get(choices[0], "finish_reason")


def _serializable_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _serializable_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable_value(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _serializable_value(model_dump(mode="json"))
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _serializable_value(to_dict())
    return str(value)


def batch_chat_with_metadata(
    model_name: str,
    messages_list: Sequence[Sequence[dict[str, Any]]],
    *,
    completion_window: str = "24h",
    poll_interval: float = 30.0,
    timeout: float | None = None,
    metadata: dict[str, str] | None = None,
    state_path: Path | str | None = None,
    retry_failed_individually: bool = True,
    retry_failed_in_batch: bool = False,
    progress: BatchProgressFn | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    if not messages_list:
        return []

    provider, requested_model, _ = _build_chat_body(
        model_name, messages_list[0], **dict(kwargs)
    )
    if provider not in ("openai", "groq"):
        results = []
        for index, messages in enumerate(messages_list, start=1):
            results.append(chat_messages_with_metadata(model_name, messages, **kwargs))
            if progress is not None:
                progress("completed", index, len(messages_list))
        return results

    client = _get_client(provider)
    custom_ids = [f"request-{index:06d}" for index in range(len(messages_list))]
    request_index = {custom_id: index for index, custom_id in enumerate(custom_ids)}
    request_fingerprint = batch_request_fingerprint(model_name, messages_list, kwargs)
    resolved_state_path = Path(state_path) if state_path is not None else None
    jsonl_path: Path | None = None

    try:
        batch = load_batch_state(
            resolved_state_path,
            model_name=model_name,
            provider=provider,
            request_count=len(messages_list),
            custom_ids=custom_ids,
            request_fingerprint=request_fingerprint,
        )
        if batch is None:
            jsonl_path = write_batch_jsonl(model_name, messages_list, custom_ids, kwargs)
            with jsonl_path.open("rb") as batch_file:
                input_file = client.files.create(file=batch_file, purpose="batch")
            batch = client.batches.create(
                input_file_id=_obj_get(input_file, "id"),
                endpoint="/v1/chat/completions",
                completion_window=completion_window,
                metadata=metadata,
            )
            save_batch_state(
                resolved_state_path,
                model_name=model_name,
                provider=provider,
                batch=batch,
                input_file_id=_obj_get(input_file, "id"),
                request_count=len(messages_list),
                custom_ids=custom_ids,
                request_fingerprint=request_fingerprint,
            )
            if progress is not None:
                progress("submitted", 0, len(messages_list))
        batch = wait_for_batch(
            client=client,
            batch_id=_obj_get(batch, "id"),
            poll_interval=poll_interval,
            timeout=timeout,
            request_count=len(messages_list),
            progress=progress,
        )
        if _obj_get(batch, "status") in {"expired", "cancelled"}:
            clear_batch_state(resolved_state_path)
            if retry_failed_individually:
                results = []
                for index, messages in enumerate(messages_list, start=1):
                    results.append(chat_messages_with_metadata(model_name, messages, **kwargs))
                    if progress is not None:
                        progress("retrying", index, len(messages_list))
                return results
        raw_results, failures = collect_batch_results(client, batch, request_index)
        results = {
            index: _chat_response_record(
                response,
                provider=provider,
                configured_model=model_name,
                requested_model=requested_model,
                request_parameters={
                    key: value
                    for key, value in _build_chat_body(
                        model_name, messages_list[index], **dict(kwargs)
                    )[2].items()
                    if key != "messages"
                },
            )
            for index, response in raw_results.items()
        }
    except Exception as exc:
        if retry_failed_individually:
            results = []
            for index, messages in enumerate(messages_list, start=1):
                results.append(chat_messages_with_metadata(model_name, messages, **kwargs))
                if progress is not None:
                    progress("retrying", index, len(messages_list))
            return results
        failures = [
            BatchChatFailure(index=index, custom_id=custom_id, error=repr(exc))
            for custom_id, index in request_index.items()
        ]
        raise BatchChatError("Batch chat submission failed", failures) from exc
    finally:
        if jsonl_path is not None:
            jsonl_path.unlink(missing_ok=True)

    missing = [
        BatchChatFailure(index=index, custom_id=custom_id, error="missing batch result")
        for custom_id, index in request_index.items()
        if index not in results and all(failure.index != index for failure in failures)
    ]
    failures.extend(missing)

    if failures and retry_failed_in_batch:
        failure_by_index = {failure.index: failure for failure in failures}
        failed_indices = sorted(failure_by_index)
        retry_state_path = None
        if resolved_state_path is not None:
            retry_state_path = resolved_state_path.with_name(
                f"{resolved_state_path.stem}.retry{resolved_state_path.suffix}"
            )
        retry_results = batch_chat_with_metadata(
            model_name,
            [messages_list[index] for index in failed_indices],
            completion_window=completion_window,
            poll_interval=poll_interval,
            timeout=timeout,
            metadata=metadata,
            state_path=retry_state_path,
            retry_failed_individually=False,
            retry_failed_in_batch=False,
            progress=None,
            **kwargs,
        )
        for index, retry_result in zip(failed_indices, retry_results):
            results[index] = retry_result
        failures = []

    if failures and retry_failed_individually:
        failures = retry_batch_failures(
            model_name=model_name,
            messages_list=messages_list,
            kwargs=kwargs,
            results=results,
            failures=failures,
        )

    if failures:
        raise BatchChatError("One or more batch chat requests failed", failures)

    clear_batch_state(resolved_state_path)
    if progress is not None:
        progress("completed", len(messages_list), len(messages_list))
    return [results[index] for index in range(len(messages_list))]


def batch_chat(
    model_name: str,
    messages_list: Sequence[Sequence[dict[str, Any]]],
    **kwargs: Any,
) -> list[str]:
    """Return response text while retaining the metadata-capable batch path."""
    return [
        str(record["content"])
        for record in batch_chat_with_metadata(model_name, messages_list, **kwargs)
    ]


def batch_chat_prompts(
    model_name: str,
    prompts: Sequence[str],
    **kwargs: Any,
) -> list[str]:
    return batch_chat(
        model_name,
        [[{"role": "user", "content": prompt}] for prompt in prompts],
        **kwargs,
    )


def batch_chat_prompts_with_metadata(
    model_name: str,
    prompts: Sequence[str],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return batch_chat_with_metadata(
        model_name,
        [[{"role": "user", "content": prompt}] for prompt in prompts],
        **kwargs,
    )


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=5, min=1, max=90),
)
def retrieve_batch(client: Any, batch_id: str) -> Any:
    return client.batches.retrieve(batch_id)


def load_batch_state(
    state_path: Path | None,
    model_name: str,
    provider: str,
    request_count: int,
    custom_ids: Sequence[str],
    request_fingerprint: str,
) -> Any | None:
    if state_path is None or not state_path.exists():
        return None
    data = json.loads(state_path.read_text(encoding="utf-8"))
    batch_id = data.get("batch_id")
    state_provider = data.get("provider")
    if not batch_id or state_provider not in ("openai", "groq"):
        return None
    if (
        data.get("model") != model_name
        or state_provider != provider
        or data.get("request_count") != request_count
        or data.get("custom_ids") != list(custom_ids)
        or data.get("request_fingerprint") != request_fingerprint
    ):
        clear_batch_state(state_path)
        return None
    return retrieve_batch(_get_client(state_provider), batch_id)


def save_batch_state(
    state_path: Path | None,
    model_name: str,
    provider: str,
    batch: Any,
    input_file_id: str,
    request_count: int,
    custom_ids: Sequence[str],
    request_fingerprint: str,
) -> None:
    if state_path is None:
        return
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model_name,
        "provider": provider,
        "batch_id": _obj_get(batch, "id"),
        "input_file_id": input_file_id,
        "request_count": request_count,
        "custom_ids": list(custom_ids),
        "request_fingerprint": request_fingerprint,
        "created_at": time.time(),
    }
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def batch_request_fingerprint(
    model_name: str,
    messages_list: Sequence[Sequence[dict[str, Any]]],
    kwargs: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "model": model_name,
            "messages": messages_list,
            "kwargs": kwargs,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clear_batch_state(state_path: Path | None) -> None:
    if state_path is not None:
        state_path.unlink(missing_ok=True)


def write_batch_jsonl(
    model_name: str,
    messages_list: Sequence[Sequence[dict[str, Any]]],
    custom_ids: Sequence[str],
    kwargs: dict[str, Any],
) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".jsonl",
        delete=False,
    )
    path = Path(handle.name)
    with handle:
        for custom_id, messages in zip(custom_ids, messages_list):
            _, _, body = _build_chat_body(model_name, messages, **dict(kwargs))
            request = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": body,
            }
            handle.write(json.dumps(request, ensure_ascii=False) + "\n")
    return path


def wait_for_batch(
    client: Any,
    batch_id: str,
    poll_interval: float,
    timeout: float | None,
    request_count: int,
    progress: BatchProgressFn | None = None,
) -> Any:
    started = time.monotonic()
    terminal_statuses = {"completed", "failed", "expired", "cancelled"}

    while True:
        batch = retrieve_batch(client, batch_id)
        status = _obj_get(batch, "status")
        if progress is not None:
            counts = _obj_get(batch, "request_counts")
            completed = int(_obj_get(counts, "completed", 0) or 0)
            failed = int(_obj_get(counts, "failed", 0) or 0)
            progress(str(status), min(request_count, completed + failed), request_count)
        if status in terminal_statuses:
            return batch
        if timeout is not None and time.monotonic() - started > timeout:
            raise TimeoutError(f"Batch {batch_id} did not complete within {timeout} seconds")
        time.sleep(poll_interval)


def collect_batch_results(
    client: Any,
    batch: Any,
    request_index: dict[str, int],
) -> tuple[dict[int, Any], list[BatchChatFailure]]:
    results: dict[int, Any] = {}
    failures: list[BatchChatFailure] = []

    output_file_id = _obj_get(batch, "output_file_id")
    if output_file_id:
        for record in read_jsonl_file(client, output_file_id):
            custom_id = str(record.get("custom_id"))
            index = request_index.get(custom_id)
            if index is None:
                continue
            error = record.get("error")
            response = record.get("response")
            status_code = _obj_get(response, "status_code")
            if error or status_code != 200:
                failures.append(BatchChatFailure(index=index, custom_id=custom_id, error=error or response))
                continue
            results[index] = _obj_get(response, "body")

    error_file_id = _obj_get(batch, "error_file_id")
    if error_file_id:
        for record in read_jsonl_file(client, error_file_id):
            custom_id = str(record.get("custom_id"))
            index = request_index.get(custom_id)
            if index is None or index in results:
                continue
            failures.append(
                BatchChatFailure(
                    index=index,
                    custom_id=custom_id,
                    error=record.get("error") or record,
                )
            )

    if _obj_get(batch, "status") in {"failed", "cancelled"} and not output_file_id:
        batch_errors = _obj_get(_obj_get(batch, "errors"), "data", None) or _obj_get(batch, "errors")
        failures.extend(
            BatchChatFailure(index=index, custom_id=custom_id, error=batch_errors)
            for custom_id, index in request_index.items()
            if index not in results
        )

    return results, dedupe_failures(failures)


def read_jsonl_file(client: Any, file_id: str) -> list[dict[str, Any]]:
    content = client.files.content(file_id)
    text = response_content_text(content)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def response_content_text(content: Any) -> str:
    if isinstance(content, bytes):
        return content.decode("utf-8")
    if isinstance(content, str):
        return content
    if hasattr(content, "text"):
        text = content.text
        return text() if callable(text) else text
    if hasattr(content, "read"):
        raw = content.read()
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)
    if hasattr(content, "content"):
        raw = content.content
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)
    return str(content)


def retry_batch_failures(
    model_name: str,
    messages_list: Sequence[Sequence[dict[str, Any]]],
    kwargs: dict[str, Any],
    results: dict[int, dict[str, Any]],
    failures: Sequence[BatchChatFailure],
) -> list[BatchChatFailure]:
    remaining: list[BatchChatFailure] = []
    for failure in failures:
        try:
            results[failure.index] = chat_messages_with_metadata(
                model_name,
                messages_list[failure.index],
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001 - caller receives packaged failures.
            remaining.append(
                BatchChatFailure(
                    index=failure.index,
                    custom_id=failure.custom_id,
                    error={"batch_error": failure.error, "retry_error": repr(exc)},
                )
            )
    return remaining


def dedupe_failures(failures: Sequence[BatchChatFailure]) -> list[BatchChatFailure]:
    seen: set[int] = set()
    deduped: list[BatchChatFailure] = []
    for failure in failures:
        if failure.index in seen:
            continue
        seen.add(failure.index)
        deduped.append(failure)
    return deduped
