"""Dynamically qualify repair/interference tasks before any LLM request."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext

from ..common.paths import default_workspace
from .external_validation import ExternalPatchValidator
from .static_validation import _apply, _read_jsonl, load_source_pair


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def _fixed_variant(
    task: dict[str, Any], record: dict[str, Any], workspace: Path
) -> bytes:
    pair = load_source_pair(
        record,
        workspace / "data/benchmarks/frameworks/defects4j/project_repos",
        workspace / "data/benchmarks/repositories/bugsinpy",
        workspace / "data/benchmarks/cache/static-sources",
    )
    condition = str(task["condition"])
    if condition == "original":
        return pair.fixed
    plugins = JAVA_INTERFERENCES if task["language"] == "java" else PYTHON_INTERFERENCES
    matches = [plugin for plugin in plugins if str(plugin.slug) == condition]
    if len(matches) != 1:
        raise ValueError(f"unknown {task['language']} interference: {condition}")
    identity = f"{task['base_task_id']}:{pair.path}:{pair.class_name}"
    return _apply(
        str(task["language"]),
        pair.fixed,
        pair.class_name,
        matches[0],
        InterferenceContext(int(task["interference_seed"]), identity),
    )


def prevalidate(
    *,
    input_path: Path,
    output: Path,
    workspace: Path,
    timeout_seconds: float,
    limit: int | None = None,
    run_regression_tests: bool = True,
    task_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Retain only inputs whose buggy and fixed sides preserve benchmark behavior."""
    tasks = list(_read_jsonl(input_path))
    if task_ids:
        tasks = [task for task in tasks if str(task.get("task_id")) in task_ids]
        found = {str(task["task_id"]) for task in tasks}
        missing = sorted(task_ids - found)
        if missing:
            raise ValueError(f"unknown --task-id value(s): {', '.join(missing)}")
    if limit is not None:
        tasks = tasks[:limit]
    output.mkdir(parents=True, exist_ok=True)
    records_path = output / "prevalidation.jsonl"
    existing = list(_read_jsonl(records_path)) if records_path.is_file() else []
    by_id = {
        str(row["task_id"]): row
        for row in existing
        if row.get("run_regression_tests") is run_regression_tests
    }
    validator = ExternalPatchValidator(
        workspace,
        output,
        timeout_seconds=timeout_seconds,
        run_regression_tests=run_regression_tests,
    )
    catalog_root = workspace / "data/benchmarks/catalogs/repair-benchmarks"
    catalogs = {
        str(row["instance_id"]): row
        for name in ("defects4j", "bugsinpy")
        for row in _read_jsonl(catalog_root / f"{name}.jsonl")
    }
    for index, task in enumerate(tasks, start=1):
        task_id = str(task["task_id"])
        if task_id in by_id:
            continue
        print(f"[{index}/{len(tasks)}] prevalidate {task_id}", flush=True)
        result: dict[str, Any] = {
            "schema_version": 1,
            "task_id": task_id,
            "base_task_id": task["base_task_id"],
            "benchmark": task["benchmark"],
            "language": task["language"],
            "condition": task["condition"],
            "run_regression_tests": run_regression_tests,
        }
        try:
            buggy = validator.probe_buggy_source(task)
            fixed = _fixed_variant(task, catalogs[str(task["base_task_id"])], workspace)
            fixed_result = validator.probe_fixed_source(task, fixed.decode("utf-8"))
            usable = (
                buggy.get("compiled") is True
                and buggy.get("trigger_failure_preserved") is True
                and fixed_result.get("functional_success") is True
                and (
                    not run_regression_tests
                    or (
                        isinstance(buggy.get("regression_failure_ids"), list)
                        and buggy.get("regression_failure_count") is not None
                    )
                )
            )
            result.update(
                status="usable" if usable else "excluded",
                usable=usable,
                buggy=buggy,
                fixed=fixed_result,
                fixed_source_sha256=hashlib.sha256(fixed).hexdigest(),
            )
        except Exception as error:
            result.update(
                status="infrastructure_error",
                usable=False,
                error_type=type(error).__name__,
                error=str(error),
            )
        by_id[task_id] = result
        _write_jsonl(records_path, list(by_id.values()))
        buggy_seconds = float(result.get("buggy", {}).get("duration_seconds", 0) or 0)
        fixed_seconds = float(result.get("fixed", {}).get("duration_seconds", 0) or 0)
        print(
            f"[{index}/{len(tasks)}] done status={result['status']} "
            f"duration={buggy_seconds + fixed_seconds:.1f}s",
            flush=True,
        )

    records = [
        by_id[str(task["task_id"])] for task in tasks if str(task["task_id"]) in by_id
    ]
    qualified = [
        {
            **task,
            "dynamic_prevalidated": True,
            "prevalidation_status": "usable",
            "correctness_definition": (
                "trigger_tests_passed_and_no_new_regression_failures"
                if run_regression_tests
                else "released_trigger_tests_passed"
            ),
            "regression_baseline_failure_ids": row.get("buggy", {}).get(
                "regression_failure_ids", []
            ),
            "regression_baseline_failure_count": row.get("buggy", {}).get(
                "regression_failure_count"
            ),
        }
        for task, row in zip(tasks, records)
        if row.get("usable") is True
    ]
    _write_jsonl(output / "tasks.jsonl", qualified)
    counts = Counter(str(row["status"]) for row in records)
    report = {
        "schema_version": 1,
        "input": input_path.as_posix(),
        "input_task_count": len(tasks),
        "qualified_task_count": len(qualified),
        "excluded_task_count": len(tasks) - len(qualified),
        "status_counts": dict(sorted(counts.items())),
        "regression_policy": "full benchmark suite"
        if run_regression_tests
        else "released trigger tests only",
        "correctness_definition": (
            "trigger_tests_passed_and_no_new_regression_failures"
            if run_regression_tests
            else "released_trigger_tests_passed"
        ),
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-prevalidate-repair-tasks",
        description="Dynamically filter repair tasks before sending them to an LLM.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="validate only this task id; repeat to select multiple tasks",
    )
    parser.add_argument(
        "--trigger-tests-only",
        action="store_true",
        help="skip the full regression suite (pilot/debug use only)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()
    input_path = args.input if args.input.is_absolute() else workspace / args.input
    output = args.output if args.output.is_absolute() else workspace / args.output
    report = prevalidate(
        input_path=input_path,
        output=output,
        workspace=workspace,
        timeout_seconds=args.timeout_seconds,
        limit=args.limit,
        run_regression_tests=not args.trigger_tests_only,
        task_ids=set(args.task_ids) if args.task_ids else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
