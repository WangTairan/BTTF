from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.methods.rmc.complexity import extract_mask_json  # noqa: E402
from src.methods.rmc.prompts import (  # noqa: E402
    GENERALIST_EXAMPLES,
    GENERALIST_NEGATIVE_3SHOT_VARIANT,
    GENERALIST_POSITIVE_3SHOT_VARIANT,
    POSITIVE_GENERALIST_EXAMPLES,
    PROMPT_VARIANTS,
    build_recovery_messages,
)
from src.methods.rmc.similarity import (  # noqa: E402
    bleu_similarity,
    exact_match_similarity,
    sequence_similarity,
    token_cosine_similarity,
    token_jaccard_similarity,
)
from src.datasets.code import load_code_dataset  # noqa: E402
from src.services.llm import MODELS, chat_messages  # noqa: E402


MAX_SOURCE_CHARS = 200_000
DATASETS = {
    "mbjp": {
        "label": "MBJP",
        "path": ROOT / "datasets" / "mbjp_dev_dataset" / "readability_dataset.json",
        "language": "java",
    },
    "scalabrino": {
        "label": "Scalabrino",
        "path": ROOT / "datasets" / "scalabrino",
        "language": "java",
    },
    "jetbrains": {
        "label": "JetBrains",
        "path": ROOT / "datasets" / "jetbrains",
        "language": "java",
    },
    "dorn": {
        "label": "Dorn",
        "path": ROOT / "datasets" / "dorn",
        "language": None,
    },
    "schnappinger": {
        "label": "Schnappinger",
        "path": ROOT / "datasets" / "schnappinger",
        "language": "java",
    },
}
MODEL_LABELS = {
    "gpt41-nano": "GPT-4.1 Nano",
    "gpt5-nano": "GPT-5 Nano",
    "gpt5-mini": "GPT-5 Mini",
    "gpt54-mini": "GPT-5.4 Mini",
    "dsv4-pro": "DeepSeek V4 Pro",
    "ds-v32": "DeepSeek V3.2",
    "qwen35p": "Qwen 3.5 Plus",
    "qwen3-32b": "Qwen 3 32B",
    "gpt-oss": "GPT-OSS 120B",
    "llama3-70": "Llama 3.3 70B",
}
@lru_cache(maxsize=None)
def dataset_items(dataset_key: str) -> tuple[Any, ...]:
    try:
        definition = DATASETS[dataset_key]
    except KeyError as exc:
        raise ValueError(f"Unknown dataset: {dataset_key}") from exc
    return tuple(load_code_dataset(definition["path"]))


def item_language(dataset_key: str, item: Any) -> str:
    configured = DATASETS[dataset_key]["language"]
    return str(configured or item.metadata.get("language") or "java").lower()


def parse_request(payload: dict[str, Any]) -> tuple[str, str, str, str, str, str | None]:
    prefix = str(payload.get("prefix", ""))
    selected = str(payload.get("selected", ""))
    suffix = str(payload.get("suffix", ""))
    model = str(payload.get("model", ""))
    variant = str(payload.get("prompt_variant", "original"))
    custom_prompt = payload.get("custom_prompt")
    if custom_prompt is not None:
        custom_prompt = str(custom_prompt)
    if not selected:
        raise ValueError("Select a non-empty source region.")
    if len(prefix) + len(selected) + len(suffix) > MAX_SOURCE_CHARS:
        raise ValueError(f"Source exceeds {MAX_SOURCE_CHARS:,} characters.")
    if model not in MODELS:
        raise ValueError(f"Unknown model: {model}")
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt variant: {variant}")
    if custom_prompt is not None and not custom_prompt.strip():
        raise ValueError("Prompt cannot be empty.")
    return prefix, selected, suffix, model, variant, custom_prompt


def recovery_messages(masked_code: str, variant: str, custom_prompt: str | None) -> list[dict[str, str]]:
    if custom_prompt is not None:
        return [{"role": "user", "content": custom_prompt}]
    return build_recovery_messages(masked_code, variant=variant)


def prompt_payload(payload: dict[str, Any]) -> dict[str, Any]:
    prefix, selected, suffix, model, variant, custom_prompt = parse_request(payload)
    masked_code = f"{prefix}<mask>{suffix}"
    messages = recovery_messages(masked_code, variant, custom_prompt)
    provider = str(MODELS[model]["provider"])
    displayed_messages = [
        {**message, "role": "system"}
        if provider == "deepseek" and message.get("role") == "developer"
        else message
        for message in messages
    ]
    prompt_text = "\n\n".join(message["content"] for message in displayed_messages)
    examples = {
        GENERALIST_NEGATIVE_3SHOT_VARIANT: GENERALIST_EXAMPLES,
        GENERALIST_POSITIVE_3SHOT_VARIANT: POSITIVE_GENERALIST_EXAMPLES,
    }.get(variant, "")
    if examples and examples in prompt_text:
        system_prompt, _, mask_section = prompt_text.partition(examples)
    else:
        system_prompt, separator, suffix = prompt_text.partition(masked_code)
        mask_section = f"{masked_code}{suffix}" if separator else ""
    return {
        "masked_code": masked_code,
        "selected_text": selected,
        "messages": displayed_messages,
        "prompt_text": prompt_text,
        "system_prompt": system_prompt,
        "examples": examples,
        "mask_section": mask_section,
        "model": model,
        "prompt_variant": variant,
    }


def recover(payload: dict[str, Any]) -> dict[str, Any]:
    preview = prompt_payload(payload)
    messages = recovery_messages(
        preview["masked_code"],
        preview["prompt_variant"],
        str(payload["custom_prompt"]) if payload.get("custom_prompt") is not None else None,
    )
    started = time.monotonic()
    raw_response = chat_messages(preview["model"], messages)
    elapsed_ms = round((time.monotonic() - started) * 1000)
    parsed, extraction_failed = extract_mask_json(raw_response)
    extracted = parsed[0] if len(parsed) == 1 else ""
    similarities = static_similarities(preview["selected_text"], extracted)
    return {
        **preview,
        "raw_response": raw_response,
        "extracted_response": extracted,
        "completed_code": f"{payload.get('prefix', '')}{extracted}{payload.get('suffix', '')}" if extracted else "",
        "extraction_failed": extraction_failed,
        "recovered_mask_count": len(parsed),
        "similarity": similarities["sequence"],
        "similarities": similarities,
        "elapsed_ms": elapsed_ms,
    }


def static_similarities(original: str, recovered: str) -> dict[str, float]:
    names = ("exact", "sequence", "jaccard", "cosine", "bleu")
    if not recovered:
        return {name: 0.0 for name in names}
    return {
        "exact": exact_match_similarity(original, recovered),
        "sequence": sequence_similarity(original, recovered),
        "jaccard": token_jaccard_similarity(original, recovered),
        "cosine": token_cosine_similarity(original, recovered),
        "bleu": bleu_similarity(original, recovered),
    }


class PlaygroundHandler(BaseHTTPRequestHandler):
    server_version = "MaskPlayground/1.0"

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/api/config":
            self.send_json(
                {
                    "models": [
                        {
                            "key": key,
                            "label": MODEL_LABELS.get(key, key),
                            "provider": value["provider"],
                            "model_id": value["id"],
                        }
                        for key, value in MODELS.items()
                    ],
                    "prompt_templates": [
                        {"key": "original", "label": "Default"},
                        {"key": "generalist_negative_3shot", "label": "Generalist 3-shot · negative"},
                        {"key": "generalist_positive_3shot", "label": "Generalist 3-shot · positive"},
                    ],
                }
            )
            return
        if path == "/api/datasets":
            self.send_json(
                {
                    "datasets": [
                        {
                            "key": key,
                            "label": definition["label"],
                            "count": len(dataset_items(key)),
                        }
                        for key, definition in DATASETS.items()
                    ]
                }
            )
            return
        if path == "/api/dataset":
            query = parse_qs(parsed_url.query)
            dataset_key = query.get("dataset", [None])[0]
            if dataset_key not in DATASETS:
                self.send_error_json(HTTPStatus.BAD_REQUEST, "Unknown dataset.")
                return
            requested_id = query.get("id", [None])[0]
            items = dataset_items(dataset_key)
            if requested_id is None:
                self.send_json(
                    {
                        "samples": [
                            {
                                "id": item.task_id,
                                "lines": len(item.content.splitlines()),
                                "language": item_language(dataset_key, item),
                            }
                            for item in items
                        ]
                    }
                )
                return
            item = next((item for item in items if item.task_id == requested_id), None)
            if item is None:
                self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown dataset sample.")
                return
            self.send_json(
                {
                    "id": item.task_id,
                    "code": item.content,
                    "lines": len(item.content.splitlines()),
                    "language": item_language(dataset_key, item),
                }
            )
            return
        self.serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/prompt":
                self.send_json(prompt_payload(payload))
                return
            if path == "/api/recover":
                self.send_json(recover(payload))
                return
            self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown API endpoint.")
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc
        if length <= 0 or length > MAX_SOURCE_CHARS * 4:
            raise ValueError("Invalid request size.")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        target = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT not in target.parents and target != STATIC_ROOT:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Not found.")
            return
        if not target.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Not found.")
            return
        content = target.read_bytes()
        mime_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"error": message}, status=status)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the mask recovery playground.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), PlaygroundHandler)
    print(f"Mask Recovery Lab: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
