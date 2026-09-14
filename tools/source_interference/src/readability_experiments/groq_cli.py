from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .common.paths import default_results, default_workspace
from .deepseek_cli import _DYNAMIC_PATCH_KINDS, evaluate_run
from .providers.groq import (
    BATCH_MODELS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_TEMPERATURE,
    GroqBatchClient,
    batch_request,
)
from .results import RunStore

_TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def _selected_tasks(args: argparse.Namespace) -> list[dict[str, Any]]:
    if not args.input.is_file():
        raise FileNotFoundError(f"task manifest not found: {args.input}")
    tasks = _read_jsonl(args.input)
    if args.task_ids:
        wanted = set(args.task_ids)
        tasks = [task for task in tasks if str(task.get("task_id")) in wanted]
        missing = wanted - {str(task.get("task_id")) for task in tasks}
        if missing:
            raise ValueError(
                f"unknown --task-id value(s): {', '.join(sorted(missing))}"
            )
    if args.limit is not None:
        tasks = tasks[: args.limit]
    malformed = [
        i + 1
        for i, task in enumerate(tasks)
        if "task_id" not in task or "prompt" not in task
    ]
    if malformed:
        raise ValueError(f"input records lack task_id or prompt: {malformed[:10]}")
    unvalidated = [
        str(task["task_id"])
        for task in tasks
        if task.get("expected_kind") in _DYNAMIC_PATCH_KINDS
        and task.get("dynamic_prevalidated") is not True
    ]
    if unvalidated and not args.allow_unvalidated_input:
        raise ValueError(
            f"repair input was not dynamically prevalidated: {unvalidated[0]}"
        )
    return tasks


def _configuration(
    args: argparse.Namespace, tasks: list[dict[str, Any]]
) -> dict[str, Any]:
    kinds = {str(task.get("expected_kind")) for task in tasks}
    lightweight = bool(kinds) and kinds <= {
        "lightweight_patch_validation",
        "lightweight_completion_validation",
    }
    return {
        "provider": "Groq Batch API",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": args.model,
        "message_roles": ["user"],
        "reasoning_effort": args.reasoning_effort,
        "include_reasoning": True,
        "temperature": args.temperature,
        "max_completion_tokens": args.max_completion_tokens,
        "batch_size": args.batch_size,
        "completion_window": args.completion_window,
        "correctness_definition": (
            "official_standalone_tests_passed"
            if lightweight
            else "trigger_tests_passed_and_no_new_regression_failures"
        ),
        "input": args.input.as_posix(),
    }


def _request_rows(
    tasks: list[dict[str, Any]], args: argparse.Namespace
) -> list[dict[str, Any]]:
    return [
        batch_request(
            custom_id=f"request-{index:06d}",
            prompt=str(task["prompt"]),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            max_completion_tokens=args.max_completion_tokens,
            temperature=args.temperature,
        )
        for index, task in enumerate(tasks)
    ]


def submit(args: argparse.Namespace) -> dict[str, Any]:
    tasks = _selected_tasks(args)
    if not tasks:
        raise ValueError("no tasks selected")
    configuration = _configuration(args, tasks)
    if args.resume_run:
        store = RunStore(args.resume_run)
        if _read_jsonl(store.directory / "tasks.jsonl") != tasks:
            raise ValueError(
                "--input selection does not match the task snapshot in --resume-run"
            )
        metadata_path = store.directory / "run.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        jobs_path = store.directory / "batch-jobs.jsonl"
        if jobs_path.is_file() and metadata.get("configuration") != configuration:
            raise ValueError(
                "batch configuration cannot change after a job has been submitted"
            )
        if not jobs_path.is_file() and metadata.get("configuration") != configuration:
            metadata["configuration"] = configuration
            temporary = metadata_path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            temporary.replace(metadata_path)
    else:
        store = RunStore.create(
            args.output_root,
            args.input.stem,
            tasks,
            configuration,
            secret_sources=["GROQ_API_KEY"],
        )
    requests = _request_rows(tasks, args)
    mapping = [
        {
            "custom_id": request["custom_id"],
            "task_id": task["task_id"],
            "model": args.model,
        }
        for request, task in zip(requests, tasks)
    ]
    _write_jsonl(store.directory / "batch-requests.jsonl", mapping)
    input_dir = store.directory / "batch-inputs"
    chunks = [
        requests[start : start + args.batch_size]
        for start in range(0, len(requests), args.batch_size)
    ]
    for index, chunk in enumerate(chunks):
        path = input_dir / f"batch-{index:04d}.jsonl"
        _write_jsonl(path, chunk)
        if path.stat().st_size > 200_000_000:
            raise ValueError(f"batch input exceeds Groq's 200 MB limit: {path}")
    if args.prepare_only:
        return {
            "run_directory": store.directory.as_posix(),
            "tasks": len(tasks),
            "batches_prepared": len(chunks),
            "submitted": 0,
        }

    jobs_path = store.directory / "batch-jobs.jsonl"
    jobs = _read_jsonl(jobs_path) if jobs_path.is_file() else []
    submitted_indexes = {int(job["batch_index"]) for job in jobs}
    client = GroqBatchClient(timeout_seconds=args.timeout_seconds)
    for index in range(len(chunks)):
        if index in submitted_indexes:
            print(
                f"[{index + 1}/{len(chunks)}] skip submitted batch",
                file=sys.stderr,
                flush=True,
            )
            continue
        input_path = input_dir / f"batch-{index:04d}.jsonl"
        print(
            f"[{index + 1}/{len(chunks)}] upload {input_path.name}",
            file=sys.stderr,
            flush=True,
        )
        uploaded = client.upload_batch_file(input_path)
        created = client.create_batch(str(uploaded["id"]), args.completion_window)
        jobs.append(
            {
                "batch_index": index,
                "request_count": len(chunks[index]),
                "input_path": input_path.relative_to(store.directory).as_posix(),
                "input_file_id": uploaded["id"],
                "batch_id": created["id"],
                "status": created.get("status"),
                "raw_batch": created,
            }
        )
        _write_jsonl(jobs_path, jobs)
        print(
            f"[{index + 1}/{len(chunks)}] submitted {created['id']}",
            file=sys.stderr,
            flush=True,
        )
    return {
        "run_directory": store.directory.as_posix(),
        "tasks": len(tasks),
        "batches_prepared": len(chunks),
        "submitted": len(jobs),
    }


def refresh_jobs(run_directory: Path, client: GroqBatchClient) -> list[dict[str, Any]]:
    path = run_directory / "batch-jobs.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"batch job manifest not found: {path}")
    jobs = _read_jsonl(path)
    for job in jobs:
        remote = client.retrieve_batch(str(job["batch_id"]))
        job["status"] = remote.get("status")
        job["output_file_id"] = remote.get("output_file_id")
        job["error_file_id"] = remote.get("error_file_id")
        job["request_counts"] = remote.get("request_counts")
        job["raw_batch"] = remote
    _write_jsonl(path, jobs)
    return jobs


def status(args: argparse.Namespace) -> dict[str, Any]:
    jobs = refresh_jobs(
        args.run_directory, GroqBatchClient(timeout_seconds=args.timeout_seconds)
    )
    counts: dict[str, int] = {}
    for job in jobs:
        value = str(job.get("status"))
        counts[value] = counts.get(value, 0) + 1
    return {
        "run_directory": args.run_directory.as_posix(),
        "batches": len(jobs),
        "statuses": counts,
    }


def _response_record(
    line: dict[str, Any], mapping: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    request = mapping.get(str(line.get("custom_id")))
    response = line.get("response") or {}
    body = response.get("body") or {}
    if (
        request is None
        or int(response.get("status_code") or 0) != 200
        or not body.get("choices")
    ):
        return None
    choice = body["choices"][0]
    message = choice.get("message") or {}
    finish_reason = choice.get("finish_reason")
    answer = str(message.get("content") or "")
    return {
        "task_id": request["task_id"],
        "answer": answer,
        "correct": None,
        "inference_status": (
            "completed"
            if finish_reason == "stop" and answer.strip()
            else f"incomplete_{finish_reason or 'unknown'}"
        ),
        "raw_response": body,
        "usage": dict(body.get("usage") or {}),
        "response_id": body.get("id") or response.get("request_id"),
        "model": str(body.get("model") or request["model"]),
    }


def _is_complete_response(record: dict[str, Any]) -> bool:
    choice = (record.get("raw_response", {}).get("choices") or [{}])[0]
    return choice.get("finish_reason") == "stop" and bool(
        str(record.get("answer") or "").strip()
    )


def collect(args: argparse.Namespace) -> dict[str, Any]:
    store = RunStore(args.run_directory)
    client = GroqBatchClient(timeout_seconds=args.timeout_seconds)
    jobs = refresh_jobs(args.run_directory, client)
    raw_dir = args.run_directory / "batch-results"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        index = int(job["batch_index"])
        output_id = job.get("output_file_id")
        error_id = job.get("error_file_id")
        output_path = raw_dir / f"batch-{index:04d}-output.jsonl"
        error_path = raw_dir / f"batch-{index:04d}-errors.jsonl"
        if output_id and not output_path.is_file():
            output_path.write_bytes(client.download_file(str(output_id)))
        if error_id and not error_path.is_file():
            error_path.write_bytes(client.download_file(str(error_id)))

    mapping = {
        row["custom_id"]: row
        for row in _read_jsonl(args.run_directory / "batch-requests.jsonl")
    }
    records_by_custom_id: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("batch-*-output.jsonl")):
        for line in _read_jsonl(path):
            record = _response_record(line, mapping)
            if record is None:
                failures.append(line)
            else:
                records_by_custom_id[str(line["custom_id"])] = record
    for path in sorted(raw_dir.glob("batch-*-errors.jsonl")):
        failures.extend(_read_jsonl(path))
    order = {
        str(row["task_id"]): index
        for index, row in enumerate(_read_jsonl(args.run_directory / "tasks.jsonl"))
    }
    records = list(records_by_custom_id.values())
    records.sort(key=lambda row: order.get(str(row["task_id"]), len(order)))
    store.replace_responses(records)
    _write_jsonl(args.run_directory / "batch-errors.jsonl", failures)
    incomplete_records = [
        record for record in records if not _is_complete_response(record)
    ]
    _write_jsonl(args.run_directory / "inference-failures.jsonl", incomplete_records)

    all_terminal = all(str(job.get("status")) in _TERMINAL_STATUSES for job in jobs)
    expected = len(mapping)
    complete_responses = sum(_is_complete_response(record) for record in records)
    collection_complete = all_terminal and len(records) == expected
    result: dict[str, Any] = {
        "run_directory": args.run_directory.as_posix(),
        "responses_collected": len(records),
        "responses_expected": expected,
        "complete_responses": complete_responses,
        "incomplete_responses": len(records) - complete_responses,
        "failed_attempts": len(failures),
        "unresolved_requests": expected - complete_responses,
        "all_batches_terminal": all_terminal,
        "complete": collection_complete,
    }
    if collection_complete:
        if args.skip_validation:
            result["summary"] = store.finalize()["overall"]
        else:
            result["summary"] = evaluate_run(
                args.run_directory,
                workspace=args.workspace,
                validation_timeout_seconds=args.validation_timeout_seconds,
                force=args.force_validation,
                run_regression_tests=True,
            )["overall"]
    return result


def retry_missing(args: argparse.Namespace) -> dict[str, Any]:
    """Submit only requests that have no successful output in this run."""
    root = args.run_directory
    mapping_rows = _read_jsonl(root / "batch-requests.jsonl")
    mapping = {str(row["custom_id"]): row for row in mapping_rows}
    tasks = {str(row["task_id"]): row for row in _read_jsonl(root / "tasks.jsonl")}
    successful: set[str] = set()
    for path in sorted((root / "batch-results").glob("batch-*-output.jsonl")):
        for line in _read_jsonl(path):
            record = _response_record(line, mapping)
            if record is not None and _is_complete_response(record):
                successful.add(str(line.get("custom_id")))
    missing = [custom_id for custom_id in mapping if custom_id not in successful]
    if not missing:
        return {"run_directory": root.as_posix(), "missing": 0, "submitted": 0}

    jobs_path = root / "batch-jobs.jsonl"
    jobs = _read_jsonl(jobs_path)
    scheduled: set[str] = set()
    for job in jobs:
        if not job.get("retry"):
            continue
        input_path = root / str(job["input_path"])
        if input_path.is_file():
            scheduled.update(str(row["custom_id"]) for row in _read_jsonl(input_path))
    pending = [custom_id for custom_id in missing if custom_id not in scheduled]
    if not pending:
        return {
            "run_directory": root.as_posix(),
            "missing": len(missing),
            "already_resubmitted": len(missing),
            "submitted": 0,
        }

    metadata_path = root / "run.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    config = dict(metadata["configuration"])
    model = str(config["model"])
    requests = []
    for custom_id in pending:
        task_id = str(mapping[custom_id]["task_id"])
        requests.append(
            batch_request(
                custom_id=custom_id,
                prompt=str(tasks[task_id]["prompt"]),
                model=model,
                reasoning_effort=str(config["reasoning_effort"]),
                max_completion_tokens=args.max_completion_tokens,
                temperature=float(config["temperature"]),
            )
        )
    chunks = [
        requests[start : start + args.batch_size]
        for start in range(0, len(requests), args.batch_size)
    ]
    client = GroqBatchClient(timeout_seconds=args.timeout_seconds)
    first_index = max((int(job["batch_index"]) for job in jobs), default=-1) + 1
    submitted = 0
    for offset, chunk in enumerate(chunks):
        index = first_index + offset
        input_path = root / "batch-inputs" / f"batch-{index:04d}.jsonl"
        _write_jsonl(input_path, chunk)
        print(
            f"[{offset + 1}/{len(chunks)}] upload retry {input_path.name}",
            file=sys.stderr,
            flush=True,
        )
        uploaded = client.upload_batch_file(input_path)
        created = client.create_batch(str(uploaded["id"]), args.completion_window)
        custom_ids = [str(row["custom_id"]) for row in chunk]
        jobs.append(
            {
                "batch_index": index,
                "request_count": len(chunk),
                "input_path": input_path.relative_to(root).as_posix(),
                "input_file_id": uploaded["id"],
                "batch_id": created["id"],
                "status": created.get("status"),
                "retry": True,
                "retry_reason": "original request exceeded Groq batch OTPM limit",
                "max_completion_tokens": args.max_completion_tokens,
                "custom_id_sha256": hashlib.sha256(
                    "\n".join(custom_ids).encode()
                ).hexdigest(),
                "raw_batch": created,
            }
        )
        _write_jsonl(jobs_path, jobs)
        submitted += len(chunk)
        print(
            f"[{offset + 1}/{len(chunks)}] submitted {created['id']}",
            file=sys.stderr,
            flush=True,
        )
    metadata["configuration"]["retry_max_completion_tokens"] = (
        args.max_completion_tokens
    )
    metadata["configuration"]["retry_reason"] = "Groq batch OTPM limit"
    temporary = metadata_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(metadata_path)
    return {
        "run_directory": root.as_posix(),
        "missing": len(missing),
        "submitted": submitted,
        "retry_batches": len(chunks),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-groq",
        description="Run validated readability tasks through the official Groq Batch API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    submit_parser = commands.add_parser(
        "submit", help="prepare, upload, and submit batch jobs"
    )
    submit_parser.add_argument("--input", type=Path, required=True)
    submit_parser.add_argument(
        "--output-root", type=Path, default=default_results("groq")
    )
    submit_parser.add_argument("--resume-run", type=Path)
    submit_parser.add_argument("--model", choices=BATCH_MODELS, default=DEFAULT_MODEL)
    submit_parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high"),
        default=DEFAULT_REASONING_EFFORT,
    )
    submit_parser.add_argument(
        "--max-completion-tokens", type=int, default=DEFAULT_MAX_COMPLETION_TOKENS
    )
    submit_parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    submit_parser.add_argument("--batch-size", type=int, default=1000)
    # Groq's prose currently mentions windows up to 7d, but its production
    # endpoint rejects `7d`; 24h is the documented example and API-tested value.
    submit_parser.add_argument("--completion-window", choices=("24h",), default="24h")
    submit_parser.add_argument("--timeout-seconds", type=float, default=120.0)
    submit_parser.add_argument("--limit", type=int)
    submit_parser.add_argument("--task-id", action="append", dest="task_ids")
    submit_parser.add_argument("--allow-unvalidated-input", action="store_true")
    submit_parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="write batch files without API calls",
    )

    status_parser = commands.add_parser("status", help="refresh batch job status")
    status_parser.add_argument("--run-directory", type=Path, required=True)
    status_parser.add_argument("--timeout-seconds", type=float, default=120.0)

    collect_parser = commands.add_parser(
        "collect", help="download responses and run official tests when complete"
    )
    collect_parser.add_argument("--run-directory", type=Path, required=True)
    collect_parser.add_argument("--timeout-seconds", type=float, default=120.0)
    collect_parser.add_argument("--workspace", type=Path, default=default_workspace())
    collect_parser.add_argument(
        "--validation-timeout-seconds", type=float, default=30.0
    )
    collect_parser.add_argument("--skip-validation", action="store_true")
    collect_parser.add_argument("--force-validation", action="store_true")

    retry_parser = commands.add_parser(
        "retry-missing", help="resubmit requests without a successful output"
    )
    retry_parser.add_argument("--run-directory", type=Path, required=True)
    retry_parser.add_argument(
        "--max-completion-tokens", type=int, default=DEFAULT_MAX_COMPLETION_TOKENS
    )
    retry_parser.add_argument("--batch-size", type=int, default=500)
    retry_parser.add_argument("--completion-window", choices=("24h",), default="24h")
    retry_parser.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "submit":
        if args.batch_size <= 0 or args.batch_size > 50_000:
            raise ValueError("--batch-size must be between 1 and 50000")
        result = submit(args)
    elif args.command == "status":
        result = status(args)
    elif args.command == "collect":
        result = collect(args)
    else:
        if args.batch_size <= 0 or args.batch_size > 50_000:
            raise ValueError("--batch-size must be between 1 and 50000")
        result = retry_missing(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
