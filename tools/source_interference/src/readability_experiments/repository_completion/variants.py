"""Build natively validated interference variants for repository holes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from readability_data.python_degradation.registry import ORDERED
from readability_data.shared.contracts import InterferenceContext
from readability_experiments.common.paths import default_workspace

from .builder import HOLE, _read_jsonl, _run_test, _write_jsonl, source_with_completion
from .catalog import REPOSITORIES
from .discovery import verify_manifest
from .prompts import span_completion_prompt
from .tasks import EXPECTED_KIND, SPAN_KEYS

SEED = 20260823
BUILDER_VERSION = "repository-completion-interference-v3"
PREVIOUS_BUILDER_VERSION = "repository-completion-interference-v2"
SCOPED_IDENTIFIER_CONDITIONS = {
    "shorten-identifiers",
    "mislead-identifiers",
    "garble-identifiers",
}
START_NAME = "__READABILITY_HOLE_START__"
END_NAME = "__READABILITY_HOLE_END__"
START = START_NAME + "()"
END = END_NAME + "()"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _span_parts(source: str, span: dict[str, Any]) -> tuple[str, str, str]:
    encoded = source.encode("utf-8")
    start = int(span["start_byte"])
    end = int(span["end_byte"])
    prefix = encoded[:start].decode("utf-8")
    raw = encoded[start:end].decode("utf-8")
    suffix = encoded[end:].decode("utf-8")
    indent = prefix[prefix.rfind("\n") + 1 :]
    if indent.strip():
        raise ValueError("completion span does not start after indentation only")
    if not raw:
        raise ValueError("completion span is empty")
    return prefix, raw, suffix


def envelope_source(source: str, span: dict[str, Any]) -> str:
    """Surround a completion with protected, parseable statement markers."""
    prefix, completion, suffix = _span_parts(source, span)
    indent = prefix[prefix.rfind("\n") + 1 :]
    # Preserve the completion bytes exactly. In particular, blank lines inside
    # docstrings must not acquire indentation merely because markers were
    # inserted around the span.
    envelope = f"{START}\n{indent}{completion}\n{indent}{END}"
    return prefix + envelope + suffix


def unwrap_envelope(source: str) -> tuple[str, str]:
    """Return the transformed gold source and the matching holed prompt source."""
    start_matches = list(
        re.finditer(rf"(?m)^(?P<indent>[ \t]*){re.escape(START)}[ \t]*\r?$", source)
    )
    end_matches = list(
        re.finditer(rf"(?m)^(?P<indent>[ \t]*){re.escape(END)}[ \t]*\r?$", source)
    )
    if len(start_matches) != 1 or len(end_matches) != 1:
        raise ValueError("interference did not preserve exactly one marker pair")
    start = start_matches[0]
    end = end_matches[0]
    if start.end() >= end.start() or start.group("indent") != end.group("indent"):
        raise ValueError("interference moved or misaligned the marker pair")
    start_line_end = source.find("\n", start.end())
    if start_line_end < 0:
        raise ValueError("start marker has no following completion line")
    content_start = start_line_end + 1
    end_line_start = end.start()
    end_line_end = source.find("\n", end.end())
    end_line_end = len(source) if end_line_end < 0 else end_line_end + 1
    completion = source[content_start:end_line_start]
    prefix = source[: start.start()]
    suffix = source[end_line_end:]
    gold_source = prefix + completion + suffix
    prompt_source = prefix + start.group("indent") + HOLE + "\n" + suffix
    return gold_source, prompt_source


def _task(
    *,
    row: dict[str, Any],
    granularity: str,
    condition: str,
    category: str,
    stats: dict[str, int],
    prompt_source: str,
    gold_source: str,
    fingerprint: str,
) -> dict[str, Any]:
    repository_id = str(row["repository_id"])
    base_task_id = (
        f"recent-completion--{repository_id}--{row['target_id']}--"
        f"{granularity.replace('_', '-')}"
    )
    return {
        "schema_version": 1,
        "build_fingerprint": fingerprint,
        "task_id": f"{base_task_id}--{condition}",
        "base_task_id": base_task_id,
        "experiment": "recent-repository-span-completion",
        "condition": condition,
        "interference_category": category,
        "interference_seed": SEED,
        "interference_stats": stats,
        "expected_kind": EXPECTED_KIND,
        "dynamic_prevalidated": True,
        "repository_id": repository_id,
        "repository_url": row["repository_url"],
        "license_spdx": row["license_spdx"],
        "language": row["language"],
        "pinned_commit": row["pinned_commit"],
        "target_origin_commit": row["method_origin_commit"],
        "target_origin_date": row["method_origin_date"],
        "target_id": row["target_id"],
        "qualified_name": row["qualified_name"],
        "source_path": row["source_path"],
        "source_sha256": row["source_sha256"],
        "granularity": granularity,
        "source_with_hole": prompt_source,
        "prompt_source_sha256": _sha256(prompt_source),
        "gold_source_sha256": _sha256(gold_source),
        "test_command": row["test_command"],
        "test_paths": row["test_paths"],
        "prompt_template": "repository-span-completion-v1",
        "prompt": span_completion_prompt(
            language=str(row["language"]),
            repository=repository_id,
            source_path=str(row["source_path"]),
            source_with_hole=prompt_source,
        ),
    }


def _fingerprint(
    row: dict[str, Any], granularity: str, condition: str, prompt_source: str
) -> str:
    payload = {
        # Version only the conditions whose construction changed.  This lets the
        # incremental builder reuse native-test results for every unaffected
        # interference while forcing the three scoped identifier variants through
        # validation again.
        "builder_version": (
            BUILDER_VERSION
            if condition in SCOPED_IDENTIFIER_CONDITIONS
            else PREVIOUS_BUILDER_VERSION
        ),
        "source_sha256": row["source_sha256"],
        "target_id": row["target_id"],
        "granularity": granularity,
        "condition": condition,
        "prompt_source_sha256": _sha256(prompt_source),
    }
    return _sha256(json.dumps(payload, sort_keys=True))


def _without_output(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    copy = dict(result)
    return copy, str(copy.pop("output"))


def _validation_hole(prompt_source: str, granularity: str) -> str:
    replacement = (
        'raise NotImplementedError("__READABILITY_HOLE__")'
        if granularity == "method_body"
        else "pass"
    )
    return source_with_completion(prompt_source, replacement)


def build_variants(
    *,
    workspace: Path,
    targets_path: Path,
    holes_path: Path,
    output: Path,
    limit_targets: int | None,
    timeout_seconds: float,
    replace: bool,
) -> dict[str, Any]:
    verification = verify_manifest(workspace, targets_path)
    usable_holes = {
        (str(row["target_id"]), str(row["granularity"]))
        for row in _read_jsonl(holes_path)
        if row.get("language") == "python"
        and row.get("status") == "usable"
        and row.get("test_sensitive") is True
    }
    rows = [
        row
        for row in _read_jsonl(targets_path)
        if row.get("language") == "python"
        and any((str(row["target_id"]), kind) in usable_holes for kind in SPAN_KEYS)
    ]
    if limit_targets is not None:
        rows = rows[:limit_targets]

    output.mkdir(parents=True, exist_ok=True)
    logs = output / "validation-logs"
    logs.mkdir(parents=True, exist_ok=True)
    validation_path = output / "validation.jsonl"
    tasks_path = output / "tasks.jsonl"
    existing_validation = {} if replace else {
        (str(item["base_task_id"]), str(item["condition"])): item
        for item in _read_jsonl(validation_path)
    }
    existing_tasks = {} if replace else {
        (str(item["base_task_id"]), str(item["condition"])): item
        for item in _read_jsonl(tasks_path)
    }
    validation: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    specs = {spec.repository_id: spec for spec in REPOSITORIES}

    for target_index, row in enumerate(rows, 1):
        repository_id = str(row["repository_id"])
        repository = (
            workspace / "data/raw/completion_pilot" / specs[repository_id].directory
        )
        source_path = repository / str(row["source_path"])
        source = source_path.read_text(encoding="utf-8")
        command = [
            str(part)
            .replace("${WORKSPACE}", str(workspace))
            .replace("${REPOSITORY}", str(repository))
            for part in row["test_command"]
        ]
        for granularity, span_key in SPAN_KEYS.items():
            if (str(row["target_id"]), granularity) not in usable_holes:
                continue
            enveloped = envelope_source(source, dict(row[span_key]))
            original_gold, original_prompt = unwrap_envelope(enveloped)
            if original_gold != source:
                raise ValueError(
                    f"marker round trip changed {row['target_id']}:{granularity}"
                )
            conditions: list[tuple[str, str, dict[str, int], str, str]] = [
                ("original", "original", {}, original_gold, original_prompt)
            ]
            protected = (
                START_NAME,
                END_NAME,
                str(row.get("symbol") or str(row["qualified_name"]).split(".")[-1]),
            )
            identity = (
                f"recent-completion:{repository_id}:{row['pinned_commit']}:"
                f"{row['source_path']}:{row['target_id']}:{granularity}"
            )
            for plugin in ORDERED:
                transformed = plugin.apply(
                    enveloped,
                    InterferenceContext(
                        seed=SEED,
                        identity=identity,
                        protected_names=protected,
                    ),
                )
                if transformed.content == enveloped:
                    continue
                try:
                    gold_source, prompt_source = unwrap_envelope(transformed.content)
                except ValueError:
                    continue
                if prompt_source == original_prompt:
                    continue
                conditions.append(
                    (
                        str(plugin.slug),
                        str(plugin.category),
                        transformed.stats,
                        gold_source,
                        prompt_source,
                    )
                )

            seen_prompts: set[str] = set()
            base_task_id = (
                f"recent-completion--{repository_id}--{row['target_id']}--"
                f"{granularity.replace('_', '-')}"
            )
            for condition, category, stats, gold_source, prompt_source in conditions:
                prompt_hash = _sha256(prompt_source)
                if prompt_hash in seen_prompts:
                    continue
                seen_prompts.add(prompt_hash)
                fingerprint = _fingerprint(
                    row, granularity, condition, prompt_source
                )
                key = (base_task_id, condition)
                previous = existing_validation.get(key)
                if previous and previous.get("build_fingerprint") == fingerprint:
                    validation.append(previous)
                    prior_task = existing_tasks.get(key)
                    if prior_task is not None:
                        tasks.append(prior_task)
                    continue
                print(
                    f"[{target_index}/{len(rows)}] {row['qualified_name']} "
                    f"{granularity} {condition}",
                    flush=True,
                )
                if condition == "original":
                    gold_result = {"passed": True, "prevalidated": True}
                    hole_result = {"passed": False, "prevalidated": True}
                    usable = True
                    syntax_error = None
                else:
                    log_base = f"{row['target_id']}--{granularity}--{condition}"
                    validation_hole = _validation_hole(prompt_source, granularity)
                    try:
                        ast.parse(gold_source)
                        ast.parse(validation_hole)
                        syntax_error = None
                    except SyntaxError as error:
                        syntax_error = str(error)
                    if syntax_error is not None:
                        gold_result = {"passed": False, "not_run": True}
                        hole_result = {"passed": None, "not_run": True}
                    else:
                        gold_raw = _run_test(
                            repo=repository,
                            source_path=source_path,
                            candidate=gold_source,
                            command=command,
                            timeout_seconds=timeout_seconds,
                        )
                        gold_result, gold_log = _without_output(gold_raw)
                        (logs / f"{log_base}--gold.log").write_text(
                            gold_log, encoding="utf-8"
                        )
                        if gold_result["passed"]:
                            hole_raw = _run_test(
                                repo=repository,
                                source_path=source_path,
                                candidate=validation_hole,
                                command=command,
                                timeout_seconds=timeout_seconds,
                            )
                            hole_result, hole_log = _without_output(hole_raw)
                            (logs / f"{log_base}--hole.log").write_text(
                                hole_log, encoding="utf-8"
                            )
                        else:
                            hole_result = {"passed": None, "not_run": True}
                    usable = bool(gold_result["passed"] and not hole_result["passed"])
                status = (
                    "usable"
                    if usable
                    else (
                        "syntax_failed"
                        if syntax_error is not None
                        else (
                            "gold_failed"
                            if not gold_result["passed"]
                            else "hole_not_detected"
                        )
                    )
                )
                record = {
                    "schema_version": 1,
                    "build_fingerprint": fingerprint,
                    "base_task_id": base_task_id,
                    "target_id": row["target_id"],
                    "qualified_name": row["qualified_name"],
                    "granularity": granularity,
                    "condition": condition,
                    "interference_category": category,
                    "interference_stats": stats,
                    "context_changed": condition != "original",
                    "gold": gold_result,
                    "hole": hole_result,
                    "syntax_error": syntax_error,
                    "usable": usable,
                    "status": status,
                    "prompt_source_sha256": prompt_hash,
                    "gold_source_sha256": _sha256(gold_source),
                }
                validation.append(record)
                if usable:
                    tasks.append(
                        _task(
                            row=row,
                            granularity=granularity,
                            condition=condition,
                            category=category,
                            stats=stats,
                            prompt_source=prompt_source,
                            gold_source=gold_source,
                            fingerprint=fingerprint,
                        )
                    )
                _write_jsonl(validation_path, validation)
                _write_jsonl(tasks_path, tasks)

    _write_jsonl(validation_path, validation)
    _write_jsonl(tasks_path, tasks)
    statuses = Counter(str(item["status"]) for item in validation)
    report = {
        "schema_version": 1,
        "builder_version": BUILDER_VERSION,
        "seed": SEED,
        "language": "python",
        "target_count": len(rows),
        "eligible_base_hole_count": len(usable_holes),
        "selected_base_hole_count": sum(
            (str(row["target_id"]), granularity) in usable_holes
            for row in rows
            for granularity in SPAN_KEYS
        ),
        "validated_candidate_count": len(validation),
        "usable_task_count": len(tasks),
        "original_task_count": sum(item["condition"] == "original" for item in tasks),
        "perturbed_task_count": sum(item["condition"] != "original" for item in tasks),
        "status_counts": dict(sorted(statuses.items())),
        "usable_by_condition": dict(
            sorted(Counter(str(item["condition"]) for item in tasks).items())
        ),
        "model_input_contains_tests": False,
        "model_input_contains_gold_completion": False,
        "source_manifest_verification": verification,
        "task_manifest_sha256": hashlib.sha256(tasks_path.read_bytes()).hexdigest(),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and natively validate Python interference variants."
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--holes", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit-targets", type=int)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    validation = (
        workspace / "data/experiments/recent-repository-completion/native-validation"
    )
    output = (
        args.output
        or workspace
        / "data/experiments/recent-repository-completion/python-interference"
    ).resolve()
    report = build_variants(
        workspace=workspace,
        targets_path=(args.targets or validation / "qualified_targets.jsonl").resolve(),
        holes_path=(args.holes or validation / "qualified_holes.jsonl").resolve(),
        output=output,
        limit_targets=args.limit_targets,
        timeout_seconds=args.timeout_seconds,
        replace=args.replace,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
