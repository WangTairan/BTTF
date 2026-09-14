"""Build a small, executable Java/Python HumanEvalPack interference dataset."""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import statistics
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from readability_data.java_degradation.interferences.core.java import tree, walk
from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext
from readability_experiments.prompts import humanevalfix_tests_instruct_prompt

from ..common.paths import default_workspace
from .validator import LightweightPatchValidator, write_jsonl

DEFAULT_SEED = 20260823


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(record: dict[str, Any], *, fixed: bool) -> str:
    # HumanEvalFixTests deliberately uses the declaration rather than the
    # docstring-bearing synthesis prompt; its tests are the source of truth.
    return str(record["declaration"]) + str(
        record["canonical_solution"] if fixed else record["buggy_solution"]
    )


def _completion_prefix(language: str, source: str, entry_point: str) -> str:
    """Return the official generation prefix ending at the callable declaration."""
    if language == "python":
        parsed = ast.parse(source)
        functions = [
            node
            for node in ast.walk(parsed)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == entry_point
        ]
        if len(functions) != 1 or not functions[0].body:
            raise ValueError(f"cannot locate unique Python entry point: {entry_point}")
        lines = source.splitlines(keepends=True)
        return "".join(lines[: functions[0].body[0].lineno - 1])
    encoded = source.encode("utf-8")
    matches = []
    for node in walk(tree(encoded).root_node):
        if node.type != "method_declaration":
            continue
        name = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if (
            name is not None
            and body is not None
            and encoded[name.start_byte : name.end_byte].decode() == entry_point
        ):
            matches.append(body.start_byte + 1)
    if len(matches) != 1:
        raise ValueError(f"cannot locate unique Java entry point: {entry_point}")
    return encoded[: matches[0]].decode("utf-8")


def _rank(seed: int, task_number: int) -> str:
    return hashlib.sha256(f"{seed}:humanevalpack:{task_number}".encode()).hexdigest()


def _apply(
    language: str, source: str, plugin: object, context: InterferenceContext
) -> tuple[str, dict[str, int]]:
    if language == "java":
        result = plugin.apply(source.encode("utf-8"), context)  # type: ignore[attr-defined]
        return result.content.decode("utf-8"), result.stats
    result = plugin.apply(source, context)  # type: ignore[attr-defined]
    return result.content, result.stats


def _base_task(language: str, record: dict[str, Any]) -> dict[str, Any]:
    number = int(str(record["task_id"]).split("/")[-1])
    source_path = "Solution.java" if language == "java" else "solution.py"
    return {
        "benchmark": "humanevalpack",
        "language": language,
        "base_task_id": f"humanevalpack__{language}__{number}",
        "paired_problem_id": f"humanevalpack__{number}",
        "problem_number": number,
        "entry_point": record["entry_point"],
        "bug_type": record["bug_type"],
        "failure_symptoms": record["failure_symptoms"],
        "source_path": source_path,
        "test_code": record["test"],
    }


def _row_key(row: dict[str, Any]) -> str:
    return f"{row['base_task_id']}--{row['condition']}"


def _existing_rows(path: Path) -> list[dict[str, Any]]:
    return _read_jsonl(path) if path.exists() else []


def _build_base(
    language: str,
    number: int,
    record: dict[str, Any],
    output: Path,
    seed: int,
    timeout: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Transform and validate all conditions for one language/problem pair."""
    validator = LightweightPatchValidator(
        output / "validation", timeout_seconds=timeout
    )
    plugins = JAVA_INTERFERENCES if language == "java" else PYTHON_INTERFERENCES
    base = _base_task(language, record)
    buggy_original = _source(record, fixed=False)
    fixed_original = _source(record, fixed=True)
    variants: list[tuple[str, str, str, dict[str, int], dict[str, int]]] = [
        ("original", buggy_original, fixed_original, {}, {})
    ]
    validation: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for plugin in plugins:
        context = InterferenceContext(
            seed,
            f"{base['base_task_id']}:{base['source_path']}",
            protected_names=(str(record["entry_point"]),),
        )
        try:
            buggy, buggy_stats = _apply(language, buggy_original, plugin, context)
            fixed, fixed_stats = _apply(language, fixed_original, plugin, context)
        except (UnicodeError, ValueError) as error:
            validation.append(
                {
                    "schema_version": 1,
                    **base,
                    "condition": str(plugin.slug),
                    "status": "transform_error",
                    "usable": False,
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            continue
        variants.append((str(plugin.slug), buggy, fixed, buggy_stats, fixed_stats))
    for condition, buggy, fixed, buggy_stats, fixed_stats in variants:
        identity = f"{base['base_task_id']}--{condition}"
        shell = {**base, "task_id": identity, "test_code": record["test"]}
        try:
            buggy_result = validator.execute_source(shell, buggy)
            fixed_result = validator.execute_source(shell, fixed)
        except (OSError, subprocess.SubprocessError) as error:
            validation.append(
                {
                    "schema_version": 1,
                    **base,
                    "condition": condition,
                    "status": "infrastructure_error",
                    "usable": False,
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            continue
        buggy_log = buggy_result.pop("log_text")
        fixed_log = fixed_result.pop("log_text")
        log_dir = output / "validation" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{identity}--buggy.log").write_text(buggy_log, encoding="utf-8")
        (log_dir / f"{identity}--fixed.log").write_text(fixed_log, encoding="utf-8")
        changed = condition == "original" or (
            buggy != buggy_original and fixed != fixed_original
        )
        usable = bool(
            changed
            and buggy_result["compiled"]
            and not buggy_result["tests_passed"]
            and fixed_result["compiled"]
            and fixed_result["tests_passed"]
        )
        validation_row = {
            "schema_version": 1,
            **base,
            "condition": condition,
            "status": "usable"
            if usable
            else ("not_applicable" if not changed else "rejected"),
            "usable": usable,
            "buggy": buggy_result,
            "fixed": fixed_result,
            "buggy_stats": buggy_stats,
            "fixed_stats": fixed_stats,
            "buggy_sha256": hashlib.sha256(buggy.encode()).hexdigest(),
            "fixed_sha256": hashlib.sha256(fixed.encode()).hexdigest(),
        }
        validation.append(validation_row)
        if not usable:
            continue
        try:
            completion_prefix = _completion_prefix(
                language, buggy, str(record["entry_point"])
            )
        except (UnicodeError, ValueError) as error:
            # A transformation can remain executable while changing the AST
            # shape expected by HumanEvalPack's official completion protocol.
            # Such a candidate is valid Java/Python, but not a usable LLM task.
            validation_row.update(
                status="prompt_error",
                usable=False,
                error_type=type(error).__name__,
                error=str(error),
            )
            continue
        tasks.append(
            {
                "task_id": f"repair--{identity}",
                "experiment": "lightweight-test-guided-repair",
                "expected_kind": "lightweight_completion_validation",
                "prompt_template": "humanevalfix-tests-instruct-official",
                **base,
                "condition": condition,
                "interference_seed": seed,
                "dynamic_prevalidated": True,
                "prevalidation_status": "usable",
                "correctness_definition": "official_standalone_tests_passed",
                "buggy_source": buggy,
                "completion_prefix": completion_prefix,
                "prompt": humanevalfix_tests_instruct_prompt(
                    buggy_source=buggy,
                    test_code=str(record["test"]),
                    entry_point=str(record["entry_point"]),
                    completion_prefix=completion_prefix,
                ),
            }
        )
    return validation, tasks


def build_dataset(
    source_root: Path,
    output: Path,
    *,
    count: int,
    seed: int,
    timeout: float,
    workers: int = 4,
) -> dict[str, Any]:
    raw = {
        language: {
            int(str(row["task_id"]).split("/")[-1]): row
            for row in _read_jsonl(source_root / language / "humanevalpack.jsonl")
        }
        for language in ("java", "python")
    }
    shared = sorted(
        set(raw["java"]) & set(raw["python"]), key=lambda number: _rank(seed, number)
    )
    selected = sorted(shared[:count])
    output.mkdir(parents=True, exist_ok=True)
    validation_path = output / "validation" / "validation.jsonl"
    tasks_path = output / "tasks.jsonl"
    validation_by_key = {_row_key(row): row for row in _existing_rows(validation_path)}
    tasks_by_key = {_row_key(row): row for row in _existing_rows(tasks_path)}
    condition_order = {
        language: ["original"] + [str(plugin.slug) for plugin in plugins]
        for language, plugins in (
            ("java", JAVA_INTERFERENCES),
            ("python", PYTHON_INTERFERENCES),
        )
    }
    expected_by_base = {
        f"humanevalpack__{language}__{number}": set(condition_order[language])
        for language in ("java", "python")
        for number in selected
    }
    existing_by_base: dict[str, set[str]] = {}
    for row in validation_by_key.values():
        existing_by_base.setdefault(str(row["base_task_id"]), set()).add(
            str(row["condition"])
        )
    pending = [
        (language, number)
        for language in ("java", "python")
        for number in selected
        if existing_by_base.get(f"humanevalpack__{language}__{number}", set())
        != expected_by_base[f"humanevalpack__{language}__{number}"]
    ]
    total_bases = len(selected) * 2
    completed_bases = total_bases - len(pending)

    def sort_key(row: dict[str, Any]) -> tuple[int, int, int]:
        language = str(row["language"])
        condition = str(row["condition"])
        return (
            ("java", "python").index(language),
            int(row["problem_number"]),
            condition_order[language].index(condition),
        )

    def checkpoint() -> None:
        valid_rows = sorted(validation_by_key.values(), key=sort_key)
        task_rows = sorted(tasks_by_key.values(), key=sort_key)
        write_jsonl(validation_path, valid_rows)
        write_jsonl(tasks_path, task_rows)
        progress = {
            "schema_version": 1,
            "seed": seed,
            "requested_paired_problem_count": count,
            "completed_base_task_count": completed_bases,
            "base_task_count": total_bases,
            "candidate_condition_count": len(valid_rows),
            "usable_llm_task_count": len(task_rows),
        }
        (output / "progress.json").write_text(
            json.dumps(progress, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if pending:
        print(
            f"Resuming with {completed_bases}/{total_bases} base tasks complete; validating {len(pending)} with {workers} workers.",
            flush=True,
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _build_base,
                    language,
                    number,
                    raw[language][number],
                    output,
                    seed,
                    timeout,
                ): (language, number)
                for language, number in pending
            }
            for future in concurrent.futures.as_completed(futures):
                language, number = futures[future]
                new_validation, new_tasks = future.result()
                base_id = f"humanevalpack__{language}__{number}"
                for key in [
                    key
                    for key, row in validation_by_key.items()
                    if row["base_task_id"] == base_id
                ]:
                    validation_by_key.pop(key)
                for key in [
                    key
                    for key, row in tasks_by_key.items()
                    if row["base_task_id"] == base_id
                ]:
                    tasks_by_key.pop(key)
                validation_by_key.update({_row_key(row): row for row in new_validation})
                tasks_by_key.update({_row_key(row): row for row in new_tasks})
                completed_bases += 1
                checkpoint()
                print(
                    f"[{completed_bases}/{total_bases}] {base_id}: "
                    f"{sum(row['usable'] for row in new_validation)}/{len(new_validation)} usable",
                    flush=True,
                )
    else:
        print(
            f"All {total_bases} base tasks already checkpointed; rebuilding report.",
            flush=True,
        )
    checkpoint()
    validation = sorted(validation_by_key.values(), key=sort_key)
    tasks = sorted(tasks_by_key.values(), key=sort_key)
    source_lines = [len(str(task["buggy_source"]).splitlines()) for task in tasks]
    status_counts = Counter(str(row["status"]) for row in validation)
    condition_counts = Counter(
        str(row["condition"]) for row in validation if row["usable"]
    )
    report = {
        "schema_version": 1,
        "dataset": "HumanEvalPack/HumanEvalFix",
        "task_variant": "HumanEvalFixTests",
        "prompt_template": "official default instruct",
        "languages": ["java", "python"],
        "seed": seed,
        "paired_problem_count": len(selected),
        "base_task_count": len(selected) * 2,
        "candidate_condition_count": len(validation),
        "usable_llm_task_count": len(tasks),
        "selected_problem_numbers": selected,
        "validation_status_counts": dict(sorted(status_counts.items())),
        "usable_by_condition": dict(sorted(condition_counts.items())),
        "source_lines": {
            "minimum": min(source_lines) if source_lines else None,
            "median": statistics.median(source_lines) if source_lines else None,
            "maximum": max(source_lines) if source_lines else None,
        },
        "source_urls": {
            "java": "https://raw.githubusercontent.com/bigcode-project/octopack/main/evaluation/create/humaneval-x/data/java/data/humanevalpack.jsonl",
            "python": "https://raw.githubusercontent.com/bigcode-project/octopack/main/evaluation/create/humaneval-x/data/python/data/humanevalpack.jsonl",
        },
        "source_sha256": {
            language: _sha256(source_root / language / "humanevalpack.jsonl")
            for language in ("java", "python")
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-lightweight-build",
        description="Build and dynamically validate a lightweight HumanEvalPack interference dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument(
        "--count", type=int, default=10, help="paired problem IDs to select"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="per compile or test process",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help="base tasks validated concurrently",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(
            "data/experiments/agent-readability-lightweight/source/humanevalpack"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/experiments/agent-readability-lightweight/dataset"),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()
    source_root = (
        args.source_root
        if args.source_root.is_absolute()
        else workspace / args.source_root
    )
    output = args.output if args.output.is_absolute() else workspace / args.output
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    print(
        json.dumps(
            build_dataset(
                source_root,
                output,
                count=args.count,
                seed=args.seed,
                timeout=args.timeout_seconds,
                workers=args.workers,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
