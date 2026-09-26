from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .benchmark_eval.external_validation import ExternalPatchValidator, save_evaluation
from .common.paths import default_results, default_workspace
from .lightweight_eval.validator import LightweightPatchValidator
from .prompts import behavior_prediction_prompt, test_guided_repair_prompt
from .providers.deepseek import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_THINKING,
    OFFICIAL_MODELS,
    DeepSeekClient,
    DeepSeekTransientAPIError,
)
from .repository_completion.tasks import EXPECTED_KIND as REPOSITORY_COMPLETION_KIND
from .repository_completion.validator import RepositoryCompletionValidator
from .results import RunStore

_DYNAMIC_PATCH_KINDS = {
    "external_patch_validation",
    "lightweight_patch_validation",
    "lightweight_completion_validation",
    REPOSITORY_COMPLETION_KIND,
}
DEFAULT_REQUEST_RETRIES = 5
DEFAULT_RETRY_BACKOFF_SECONDS = 1.0
_RESPONSE_MODEL_ALIASES = {
    # Preserve compatibility with old provider responses that used the
    # deployment name instead of the requested public API identifier.
    "deepseek-pro": "deepseek-v4-pro",
}


def _requested_model(row: dict[str, object]) -> str:
    """Recover the request model from old and new response records."""
    requested = row.get("requested_model")
    if requested:
        return str(requested)
    returned = str(row.get("model") or "")
    return _RESPONSE_MODEL_ALIASES.get(returned, returned)


def _patch_validator(
    expected_kind: str,
    *,
    workspace: Path,
    run_directory: Path,
    timeout_seconds: float,
    run_regression_tests: bool,
):
    if expected_kind == REPOSITORY_COMPLETION_KIND:
        return RepositoryCompletionValidator(
            run_directory,
            workspace=workspace,
            timeout_seconds=timeout_seconds,
        )
    if expected_kind == "external_patch_validation":
        return ExternalPatchValidator(
            workspace,
            run_directory,
            timeout_seconds=timeout_seconds,
            run_regression_tests=run_regression_tests,
        )
    if expected_kind in {
        "lightweight_patch_validation",
        "lightweight_completion_validation",
    }:
        return LightweightPatchValidator(
            run_directory,
            timeout_seconds=timeout_seconds,
        )
    raise ValueError(f"unsupported dynamic patch validation kind: {expected_kind}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-deepseek",
        description="Run validated readability tasks with the official DeepSeek API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke = subparsers.add_parser("smoke", help="make one minimal request per model")
    smoke.add_argument(
        "--output", type=Path, default=default_results("deepseek") / "smoke.json"
    )
    prompt_smoke = subparsers.add_parser(
        "prompt-smoke", help="run four automatically checked prompt examples per model"
    )
    prompt_smoke.add_argument(
        "--output-root",
        type=Path,
        default=default_results("deepseek"),
    )
    prompt_smoke.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    prompt_smoke.add_argument(
        "--thinking", choices=("enabled", "disabled"), default=DEFAULT_THINKING
    )
    prompt_smoke.add_argument(
        "--reasoning-effort",
        choices=("low", "high", "max"),
        default=DEFAULT_REASONING_EFFORT,
    )
    run = subparsers.add_parser("run", help="run a prompt-bearing validated task JSONL")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--output-root", type=Path, default=default_results("deepseek"))
    run.add_argument(
        "--resume-run",
        type=Path,
        help="existing run directory to continue instead of creating a new run",
    )
    run.add_argument(
        "--models", nargs="+", choices=OFFICIAL_MODELS, default=list(OFFICIAL_MODELS)
    )
    run.add_argument("--limit", type=int)
    run.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="run only this task id; repeat to select multiple tasks",
    )
    run.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    run.add_argument(
        "--length-retries",
        type=int,
        default=1,
        help="retry this many times when the provider returns finish_reason=length",
    )
    run.add_argument(
        "--request-retries",
        type=int,
        default=DEFAULT_REQUEST_RETRIES,
        help="retry transient connection, rate-limit, and server failures this many times",
    )
    run.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=DEFAULT_RETRY_BACKOFF_SECONDS,
        help="initial exponential-backoff delay for transient request failures",
    )
    run.add_argument("--timeout-seconds", type=float, default=600.0)
    run.add_argument("--workspace", type=Path, default=default_workspace())
    run.add_argument("--validation-timeout-seconds", type=float, default=900.0)
    run.add_argument(
        "--skip-external-validation",
        action="store_true",
        help="save responses without applying patches or running benchmark tests",
    )
    run.add_argument(
        "--allow-unvalidated-input",
        action="store_true",
        help="allow repair tasks that did not pass dynamic prevalidation (debug use only)",
    )
    run.add_argument(
        "--trigger-tests-only",
        action="store_true",
        help="skip full regression tests during patch evaluation (pilot/debug use only)",
    )
    run.add_argument(
        "--thinking", choices=("enabled", "disabled"), default=DEFAULT_THINKING
    )
    run.add_argument(
        "--reasoning-effort",
        choices=("low", "high", "max"),
        default=DEFAULT_REASONING_EFFORT,
    )
    evaluate = subparsers.add_parser(
        "evaluate", help="evaluate and summarize responses already saved in a run"
    )
    evaluate.add_argument("--run-directory", type=Path, required=True)
    evaluate.add_argument("--workspace", type=Path, default=default_workspace())
    evaluate.add_argument("--validation-timeout-seconds", type=float, default=900.0)
    evaluate.add_argument(
        "--force",
        action="store_true",
        help="rerun dynamic validation for already evaluated responses",
    )
    evaluate.add_argument(
        "--trigger-tests-only",
        action="store_true",
        help="skip full regression tests (pilot/debug use only)",
    )
    return parser


def _append_jsonl(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _chat_with_length_retry(
    client: DeepSeekClient,
    *,
    prompt: str,
    model: str,
    max_tokens: int,
    thinking: str,
    reasoning_effort: str,
    length_retries: int,
    request_retries: int = DEFAULT_REQUEST_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
):
    """Return the final response while retaining length and transport retries."""
    if length_retries < 0:
        raise ValueError("--length-retries must be non-negative")
    if request_retries < 0:
        raise ValueError("--request-retries must be non-negative")
    if retry_backoff_seconds < 0:
        raise ValueError("--retry-backoff-seconds must be non-negative")
    retry_history: list[dict[str, object]] = []
    transport_retry_history: list[dict[str, object]] = []

    def request():
        for attempt in range(request_retries + 1):
            try:
                return client.chat(
                    prompt,
                    model,
                    max_tokens=max_tokens,
                    thinking=thinking,
                    reasoning_effort=reasoning_effort,
                )
            except DeepSeekTransientAPIError as error:
                if attempt >= request_retries:
                    raise
                delay = min(retry_backoff_seconds * (2**attempt), 30.0)
                transport_retry_history.append(
                    {
                        "attempt": attempt + 1,
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "delay_seconds": delay,
                    }
                )
                print(
                    f"transient DeepSeek failure; retry {attempt + 1}/{request_retries} "
                    f"in {delay:g}s: {error}",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(delay)
        raise AssertionError("unreachable")

    response = request()
    for _ in range(length_retries):
        if response.finish_reason != "length":
            break
        retry_history.append(
            {
                "answer": response.content,
                "raw_response": response.raw_response,
                "usage": response.usage,
                "response_id": response.response_id,
                "model": response.model,
            }
        )
        response = request()
    return response, retry_history, transport_retry_history


def smoke(output: Path) -> list[dict[str, object]]:
    client = DeepSeekClient()
    rows = []
    prompt = 'Return exactly one JSON object with the key "status" and value "ok".'
    for model in OFFICIAL_MODELS:
        response = client.chat(
            prompt,
            model,
            max_tokens=64,
            thinking="disabled",
            reasoning_effort="low",
            json_output=True,
        )
        rows.append(
            {
                "requested_model": model,
                "called_at": datetime.now(timezone.utc).isoformat(),
                **response.as_dict(),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rows


def _prompt_smoke_tasks() -> list[dict[str, object]]:
    java_behavior_source = """public final class Calculator {
    public static int calculate(int value) {
        int doubled = value * 2;
        return doubled + 3;
    }
}"""
    java_behavior_harness = """public final class Main {
    public static void main(String[] args) {
        System.out.println(Calculator.calculate(7));
    }
}"""
    python_behavior_source = """class TextTools:
    @staticmethod
    def repeat(text, count):
        return text * count"""
    python_behavior_harness = 'print(TextTools.repeat("ab", 3))'
    java_buggy = """public final class Calculator {
    public static int add(int left, int right) {
        return left - right;
    }
}"""
    java_test = """assertEquals(7, Calculator.add(4, 3));
assertEquals(-1, Calculator.add(-2, 1));"""
    python_buggy = """def is_above_limit(value, limit):
    return value >= limit"""
    python_test = """assert is_above_limit(6, 5) is True
assert is_above_limit(5, 5) is False"""
    return [
        {
            "task_id": "behavior-java-smoke",
            "experiment": "behavior-prediction",
            "prompt": behavior_prediction_prompt(
                language="Java",
                source_path="Calculator.java",
                source_code=java_behavior_source,
                harness_code=java_behavior_harness,
            ),
            "expected_kind": "stdout_lines",
            "expected": ["17"],
        },
        {
            "task_id": "behavior-python-smoke",
            "experiment": "behavior-prediction",
            "prompt": behavior_prediction_prompt(
                language="Python",
                source_path="text_tools.py",
                source_code=python_behavior_source,
                harness_code=python_behavior_harness,
            ),
            "expected_kind": "stdout_lines",
            "expected": ["ababab"],
        },
        {
            "task_id": "repair-java-smoke",
            "experiment": "test-guided-repair",
            "prompt": test_guided_repair_prompt(
                language="Java",
                source_path="Calculator.java",
                buggy_source=java_buggy,
                test_source=java_test,
                test_command="mvn test -Dtest=CalculatorTest",
                failure_output="expected: <7> but was: <1>",
            ),
            "expected_kind": "patch_contains",
            "expected": [
                "-        return left - right;",
                "+        return left + right;",
            ],
        },
        {
            "task_id": "repair-python-smoke",
            "experiment": "test-guided-repair",
            "prompt": test_guided_repair_prompt(
                language="Python",
                source_path="limits.py",
                buggy_source=python_buggy,
                test_source=python_test,
                test_command="pytest -q test_limits.py",
                failure_output="assert True is False",
            ),
            "expected_kind": "patch_contains",
            "expected": ["-    return value >= limit", "+    return value > limit"],
        },
    ]


def _check_prompt_smoke(task: dict[str, object], content: str) -> tuple[bool, str]:
    if task["expected_kind"] == "stdout_lines":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return False, "response is not JSON"
        passed = parsed == {"stdout_lines": task["expected"]}
        return (
            passed,
            "exact JSON and stdout match" if passed else "predicted stdout mismatch",
        )
    expected = list(task["expected"])
    normalized = content.strip()
    if normalized.startswith("```") and normalized.endswith("```"):
        normalized = normalized.split("\n", 1)[1].rsplit("\n", 1)[0]
    passed = (
        normalized.startswith("--- ") or normalized.startswith("diff --git ")
    ) and all(fragment in normalized for fragment in expected)
    return (
        passed,
        "minimal change appears in unified diff"
        if passed
        else "missing unified diff or expected change",
    )


def _check_validated_task(task: dict[str, object], content: str) -> bool | None:
    if task.get("expected_kind") in _DYNAMIC_PATCH_KINDS:
        return None
    if task.get("experiment") == "behavior-prediction":
        try:
            return json.loads(content) == task.get("expected")
        except json.JSONDecodeError:
            return False
    if task.get("experiment") == "test-guided-repair":
        normalized = content.strip()
        if normalized.startswith("```diff\n") and normalized.endswith("```"):
            normalized = normalized[len("```diff\n") : -3].rstrip()
        expected = task.get("expected")
        if isinstance(expected, dict):
            removed = "-" + str(expected.get("removed_line", ""))
            added = "+" + str(expected.get("added_line", ""))
        elif task.get("mutation") == "invert_dict_equality":
            # Compatibility with the first saved pilot run.
            removed = "-        return dict(self.lower_items()) != dict(other_dict.lower_items())"
            added = "+        return dict(self.lower_items()) == dict(other_dict.lower_items())"
        else:
            return False
        return (
            (normalized.startswith("--- ") or normalized.startswith("diff --git "))
            and removed in normalized
            and added in normalized
        )
    return False


def evaluate_run(
    run_directory: Path,
    *,
    workspace: Path | None = None,
    validation_timeout_seconds: float = 900.0,
    force: bool = False,
    run_regression_tests: bool = True,
) -> dict[str, object]:
    store = RunStore(run_directory)
    tasks = {
        str(task["task_id"]): task
        for task in [
            json.loads(line)
            for line in (run_directory / "tasks.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
    }
    rows = store.responses()
    evaluations_path = run_directory / "evaluations.jsonl"
    if force:
        # A forced re-evaluation replaces obsolete validator decisions while
        # preserving the immutable provider responses and task snapshot.
        evaluations_path.write_text("", encoding="utf-8")
    validators: dict[str, object] = {}
    for row in rows:
        task = tasks.get(str(row["task_id"]))
        if task is None:
            row["correct"] = False
            continue
        choice = (row.get("raw_response", {}).get("choices") or [{}])[0]
        if choice.get("finish_reason") == "length":
            # The provider returned no completed answer within the configured
            # inference budget. Record this as a model failure without trying
            # to execute a partial completion.
            row["correct"] = False
            row["inference_status"] = "incomplete_length"
            continue
        checked = _check_validated_task(task, str(row.get("answer") or ""))
        expected_kind = str(task.get("expected_kind"))
        if checked is not None or expected_kind not in _DYNAMIC_PATCH_KINDS:
            row["correct"] = checked
            continue
        if row.get("correct") is not None and not force:
            continue
        validator = validators.get(expected_kind)
        if validator is None:
            validator = _patch_validator(
                expected_kind,
                workspace=workspace if workspace is not None else default_workspace(),
                run_directory=run_directory,
                timeout_seconds=validation_timeout_seconds,
                run_regression_tests=run_regression_tests,
            )
            validators[expected_kind] = validator
        print(
            f"validate {row.get('model')} {row['task_id']}",
            file=sys.stderr,
            flush=True,
        )
        evaluation = validator.validate(  # type: ignore[attr-defined]
            task, str(row.get("answer") or ""), str(row.get("model"))
        )
        row["correct"] = evaluation["correct"]
        save_evaluation(evaluations_path, evaluation)
        print(
            f"validated status={evaluation['status']} correct={evaluation['correct']}",
            file=sys.stderr,
            flush=True,
        )
    store.replace_responses(rows)
    return store.finalize()


def prompt_smoke(
    output_root: Path,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    thinking: str = DEFAULT_THINKING,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> tuple[RunStore, list[dict[str, object]], dict[str, object]]:
    client = DeepSeekClient()
    tasks = _prompt_smoke_tasks()
    configuration = {
        "provider": "DeepSeek official API",
        "endpoint": "https://api.deepseek.com/chat/completions",
        "models": list(OFFICIAL_MODELS),
        "message_roles": ["user"],
        "thinking": thinking,
        "reasoning_effort": reasoning_effort,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": max_tokens,
    }
    store = RunStore.create(output_root, "prompt-smoke", tasks, configuration)
    rows: list[dict[str, object]] = []
    for task in tasks:
        for model in OFFICIAL_MODELS:
            response = client.chat(
                str(task["prompt"]),
                model,
                max_tokens=max_tokens,
                thinking=thinking,
                reasoning_effort=reasoning_effort,
                json_output=task["expected_kind"] == "stdout_lines",
            )
            passed, check = _check_prompt_smoke(task, response.content)
            row = {
                "task_id": task["task_id"],
                "answer": response.content,
                "correct": passed,
                "raw_response": response.raw_response,
                "usage": response.usage,
                "response_id": response.response_id,
                "model": response.model,
            }
            store.append(row)
            rows.append(row)
    summary = store.finalize()
    return store, rows, summary


def run_tasks(args: argparse.Namespace) -> dict[str, object]:
    if not args.input.is_file():
        raise FileNotFoundError(
            f"task manifest not found: {args.input}. If this is a dynamically "
            "qualified repair manifest, run the prevalidation command first; "
            "see README.md under 'Official DeepSeek runner'."
        )
    tasks = [
        json.loads(line)
        for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.task_ids:
        requested = set(args.task_ids)
        tasks = [task for task in tasks if str(task.get("task_id")) in requested]
        found = {str(task["task_id"]) for task in tasks}
        missing_ids = sorted(requested - found)
        if missing_ids:
            raise ValueError(f"unknown --task-id value(s): {', '.join(missing_ids)}")
    if args.limit is not None:
        tasks = tasks[: args.limit]
    missing = [
        index + 1
        for index, task in enumerate(tasks)
        if "task_id" not in task or "prompt" not in task
    ]
    if missing:
        raise ValueError(
            "input must be a validated task JSONL containing task_id and prompt; "
            f"missing fields on record(s): {missing[:10]}"
        )
    unvalidated = [
        str(task["task_id"])
        for task in tasks
        if task.get("expected_kind") in _DYNAMIC_PATCH_KINDS
        and task.get("dynamic_prevalidated") is not True
    ]
    if unvalidated and not args.allow_unvalidated_input:
        raise ValueError(
            "repair inputs must pass dynamic prevalidation before model calls; "
            "run the builder/prevalidator for the selected benchmark first "
            f"(first unvalidated task: {unvalidated[0]})"
        )
    expected_kinds = {str(task.get("expected_kind")) for task in tasks}
    lightweight_only = bool(expected_kinds) and expected_kinds <= {
        "lightweight_patch_validation",
        "lightweight_completion_validation",
    }
    if expected_kinds == {REPOSITORY_COMPLETION_KIND}:
        correctness_definition = "pinned_repository_focused_tests_passed"
    elif lightweight_only:
        correctness_definition = "official_standalone_tests_passed"
    elif not args.trigger_tests_only:
        correctness_definition = "trigger_tests_passed_and_no_new_regression_failures"
    else:
        correctness_definition = "released_trigger_tests_passed"
    configuration = {
        "provider": "DeepSeek official API",
        "endpoint": "https://api.deepseek.com/chat/completions",
        "models": list(args.models),
        "message_roles": ["user"],
        "thinking": args.thinking,
        "reasoning_effort": args.reasoning_effort,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": args.max_tokens,
        "length_retries": args.length_retries,
        "request_retries": args.request_retries,
        "retry_backoff_seconds": args.retry_backoff_seconds,
        "timeout_seconds": args.timeout_seconds,
        "external_validation": not args.skip_external_validation,
        "validation_timeout_seconds": args.validation_timeout_seconds,
        "regression_tests": not args.trigger_tests_only,
        "correctness_definition": correctness_definition,
        "input": args.input.as_posix(),
    }
    if args.resume_run is not None:
        store = RunStore(args.resume_run)
        existing_tasks = [
            json.loads(line)
            for line in (store.directory / "tasks.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        if existing_tasks != tasks:
            raise ValueError("--input does not match the task snapshot in --resume-run")
    else:
        store = RunStore.create(args.output_root, args.input.stem, tasks, configuration)
    if not args.skip_external_validation and store.responses():
        # A prior process may have stopped after durably saving an API response
        # but before its benchmark test completed.
        evaluate_run(
            store.directory,
            workspace=args.workspace,
            validation_timeout_seconds=args.validation_timeout_seconds,
            run_regression_tests=not args.trigger_tests_only,
        )
    completed = {
        (str(row["task_id"]), _requested_model(row))
        for row in store.responses()
        if (row.get("raw_response", {}).get("choices") or [{}])[0].get("finish_reason")
        is not None
    }
    if completed:
        print(
            f"resume: {len(completed)} completed task/model pairs will be skipped",
            file=sys.stderr,
            flush=True,
        )
    client: DeepSeekClient | None = None
    written = 0
    skipped = 0
    total_requests = len(tasks) * len(args.models)
    request_index = 0
    validators: dict[str, object] = {}
    for task in tasks:
        for model in args.models:
            request_index += 1
            key = (str(task["task_id"]), model)
            if key in completed:
                skipped += 1
                continue
            if client is None:
                client = DeepSeekClient(timeout_seconds=args.timeout_seconds)
            print(
                f"[{request_index}/{total_requests}] request {model} {task['task_id']}",
                file=sys.stderr,
                flush=True,
            )
            response, retry_history, transport_retry_history = _chat_with_length_retry(
                client,
                prompt=str(task["prompt"]),
                model=model,
                max_tokens=args.max_tokens,
                thinking=args.thinking,
                reasoning_effort=args.reasoning_effort,
                length_retries=args.length_retries,
                request_retries=args.request_retries,
                retry_backoff_seconds=args.retry_backoff_seconds,
            )
            row = {
                "task_id": task["task_id"],
                "answer": response.content,
                "correct": _check_validated_task(task, response.content),
                "raw_response": response.raw_response,
                "usage": response.usage,
                "response_id": response.response_id,
                "model": response.model,
                "requested_model": model,
                "attempt_count": len(retry_history) + 1,
                "retry_history": retry_history,
                "transport_attempt_count": len(transport_retry_history)
                + len(retry_history)
                + 1,
                "transport_retry_history": transport_retry_history,
            }
            # Save the expensive API response before starting local build/test
            # work so an interruption never requires another model request.
            store.append(row)
            print(
                f"[{request_index}/{total_requests}] saved finish={response.finish_reason} "
                f"answer_chars={len(response.content)} total_tokens={response.usage.get('total_tokens')}",
                file=sys.stderr,
                flush=True,
            )
            expected_kind = str(task.get("expected_kind"))
            if (
                not args.skip_external_validation
                and expected_kind in _DYNAMIC_PATCH_KINDS
            ):
                validator = validators.get(expected_kind)
                if validator is None:
                    validator = _patch_validator(
                        expected_kind,
                        workspace=args.workspace,
                        run_directory=store.directory,
                        timeout_seconds=args.validation_timeout_seconds,
                        run_regression_tests=not args.trigger_tests_only,
                    )
                    validators[expected_kind] = validator
                print(
                    f"[{request_index}/{total_requests}] validate {model} {task['task_id']}",
                    file=sys.stderr,
                    flush=True,
                )
                evaluation = validator.validate(  # type: ignore[attr-defined]
                    task, response.content, response.model
                )
                row["correct"] = evaluation["correct"]
                rows = store.responses()
                rows[-1] = row
                store.replace_responses(rows)
                save_evaluation(store.directory / "evaluations.jsonl", evaluation)
                print(
                    f"[{request_index}/{total_requests}] validated "
                    f"status={evaluation['status']} correct={evaluation['correct']}",
                    file=sys.stderr,
                    flush=True,
                )
            completed.add(key)
            written += 1
    summary = store.finalize()
    return {
        "tasks": len(tasks),
        "written": written,
        "skipped_existing": skipped,
        "run_directory": store.directory.as_posix(),
        "summary": summary["overall"],
    }


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "smoke":
        rows = smoke(args.output)
        print(
            json.dumps(
                {
                    "output": args.output.as_posix(),
                    "models": [row["requested_model"] for row in rows],
                    "finish_reasons": [row["finish_reason"] for row in rows],
                },
                indent=2,
            )
        )
        return
    if args.command == "prompt-smoke":
        store, rows, summary = prompt_smoke(
            args.output_root,
            max_tokens=args.max_tokens,
            thinking=args.thinking,
            reasoning_effort=args.reasoning_effort,
        )
        print(
            json.dumps(
                {
                    "run_directory": store.directory.as_posix(),
                    "requests": len(rows),
                    "correct": summary["overall"]["correct"],
                    "incorrect": summary["overall"]["incorrect"],
                },
                indent=2,
            )
        )
        return
    if args.command == "evaluate":
        summary = evaluate_run(
            args.run_directory,
            workspace=args.workspace,
            validation_timeout_seconds=args.validation_timeout_seconds,
            force=args.force,
            run_regression_tests=not args.trigger_tests_only,
        )
        print(json.dumps(summary["overall"], indent=2))
        return
    print(json.dumps(run_tasks(args), indent=2))


if __name__ == "__main__":
    main()
