"""Natively validate method- and statement-level completion holes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from readability_data.java_degradation.interferences.core.java import tree
from readability_experiments.common.paths import default_workspace

from .builder import _read_jsonl, _run_test, _write_jsonl
from .catalog import REPOSITORIES
from .discovery import verify_manifest

VALIDATOR_VERSION = "recent-completion-native-validation-v1"
GRANULARITIES = ("method_body", "statement")


def _fingerprint(row: dict[str, Any]) -> str:
    payload = json.dumps(row, sort_keys=True) + VALIDATOR_VERSION
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _replace_span(source: str, span: dict[str, Any], replacement: str) -> str:
    encoded = source.encode("utf-8")
    start = int(span["start_byte"])
    end = int(span["end_byte"])
    return (encoded[:start] + replacement.encode("utf-8") + encoded[end:]).decode(
        "utf-8"
    )


def validation_hole_source(
    source: str, row: dict[str, Any], granularity: str
) -> str:
    language = str(row["language"])
    if granularity == "method_body":
        span = row["method_span"]
        replacement = (
            'throw new UnsupportedOperationException("__READABILITY_HOLE__");'
            if language == "java"
            else 'raise NotImplementedError("__READABILITY_HOLE__")'
        )
    elif granularity == "statement":
        span = row["statement_span"]
        # Removing a statement is the least assumptive counterfactual. It
        # preserves syntax while avoiding a fabricated default value.
        replacement = ";" if language == "java" else "pass"
    else:
        raise ValueError(f"unknown granularity: {granularity}")
    return _replace_span(source, span, replacement)


def _syntax_valid(source: str, language: str) -> tuple[bool, str | None]:
    try:
        if language == "python":
            ast.parse(source)
        elif language == "java":
            parsed = tree(source.encode("utf-8")).root_node
            if parsed.has_error:
                return False, "tree-sitter parse contains an ERROR node"
        else:
            raise ValueError(f"unsupported language: {language}")
    except (SyntaxError, ValueError) as error:
        return False, str(error)
    return True, None


def _command(
    row: dict[str, Any], *, repository: Path, workspace: Path
) -> list[str]:
    return [
        str(part)
        .replace("${WORKSPACE}", str(workspace))
        .replace("${REPOSITORY}", str(repository))
        for part in row["test_command"]
    ]


def _log_name(target_id: str, kind: str) -> str:
    return f"{target_id}--{kind}.log"


def _without_output(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    copy = dict(result)
    output = str(copy.pop("output"))
    return copy, output


def _native_failure_stage(output: str, language: str) -> str:
    if language == "java" and (
        "COMPILATION ERROR" in output
        or "Compilation failure" in output
        or "Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin"
        in output
    ):
        return "compilation"
    return "native_test"


def validate(
    *,
    workspace: Path,
    manifest: Path,
    output: Path,
    timeout_seconds: float,
    per_language: int | None,
    retain_per_language: int,
    replace: bool,
) -> dict[str, Any]:
    manifest_verification = verify_manifest(workspace, manifest)
    rows = _read_jsonl(manifest)
    if per_language is not None:
        selected: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        for row in rows:
            language = str(row["language"])
            if counts[language] >= per_language:
                continue
            selected.append(row)
            counts[language] += 1
        rows = selected

    specs = {spec.repository_id: spec for spec in REPOSITORIES}
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    target_checkpoint = output / "target_validation.jsonl"
    hole_checkpoint = output / "hole_validation.jsonl"
    existing_targets = {} if replace else {
        (str(row["target_id"]), str(row["validation_fingerprint"])): row
        for row in _read_jsonl(target_checkpoint)
    }
    existing_holes = {} if replace else {
        (
            str(row["target_id"]),
            str(row["granularity"]),
            str(row["validation_fingerprint"]),
        ): row
        for row in _read_jsonl(hole_checkpoint)
    }
    checkpoint_targets = dict(existing_targets)
    checkpoint_holes = dict(existing_holes)
    target_results: list[dict[str, Any]] = []
    hole_results: list[dict[str, Any]] = []

    for index, row in enumerate(rows, 1):
        target_id = str(row["target_id"])
        repository_id = str(row["repository_id"])
        spec = specs[repository_id]
        repository = workspace / "data/raw/completion_pilot" / spec.directory
        source_path = repository / str(row["source_path"])
        source = source_path.read_text(encoding="utf-8")
        command = _command(row, repository=repository, workspace=workspace)
        fingerprint = _fingerprint(row)
        baseline_key = (target_id, fingerprint)
        if baseline_key in existing_targets:
            baseline_row = existing_targets[baseline_key]
            print(f"[{index}/{len(rows)}] {repository_id} {row['qualified_name']}: resumed")
        else:
            print(
                f"[{index}/{len(rows)}] {repository_id} {row['qualified_name']}: baseline",
                flush=True,
            )
            baseline_raw = _run_test(
                repo=repository,
                source_path=source_path,
                candidate=source,
                command=command,
                timeout_seconds=timeout_seconds,
            )
            baseline, baseline_log = _without_output(baseline_raw)
            (logs / _log_name(target_id, "baseline")).write_text(
                baseline_log, encoding="utf-8"
            )
            baseline_row = {
                "schema_version": 1,
                "validation_fingerprint": fingerprint,
                "target_id": target_id,
                "repository_id": repository_id,
                "language": row["language"],
                "source_path": row["source_path"],
                "qualified_name": row["qualified_name"],
                "baseline": baseline,
                "status": "baseline_passed" if baseline["passed"] else "baseline_failed",
            }
        target_results.append(baseline_row)
        checkpoint_targets[baseline_key] = baseline_row
        _write_jsonl(target_checkpoint, list(checkpoint_targets.values()))

        for granularity in GRANULARITIES:
            key = (target_id, granularity, fingerprint)
            if key in existing_holes:
                resumed_hole = existing_holes[key]
                hole_results.append(resumed_hole)
                checkpoint_holes[key] = resumed_hole
                continue
            hole_source = validation_hole_source(source, row, granularity)
            syntax_valid, syntax_error = _syntax_valid(hole_source, str(row["language"]))
            hole_result: dict[str, Any] | None = None
            failure_stage = None
            test_sensitive = False
            if baseline_row["baseline"]["passed"] and syntax_valid:
                print(f"  {granularity}: native test", flush=True)
                hole_raw = _run_test(
                    repo=repository,
                    source_path=source_path,
                    candidate=hole_source,
                    command=command,
                    timeout_seconds=timeout_seconds,
                )
                hole_result, hole_log = _without_output(hole_raw)
                (logs / _log_name(target_id, granularity)).write_text(
                    hole_log, encoding="utf-8"
                )
                if hole_result["passed"]:
                    failure_stage = "not_detected"
                else:
                    failure_stage = _native_failure_stage(
                        hole_log, str(row["language"])
                    )
                    test_sensitive = failure_stage == "native_test"
            elif not baseline_row["baseline"]["passed"]:
                failure_stage = "baseline"
            else:
                failure_stage = "syntax"
            result = {
                "schema_version": 1,
                "validation_fingerprint": fingerprint,
                "target_id": target_id,
                "repository_id": repository_id,
                "language": row["language"],
                "source_path": row["source_path"],
                "qualified_name": row["qualified_name"],
                "granularity": granularity,
                "syntax_valid": syntax_valid,
                "syntax_error": syntax_error,
                "hole": hole_result,
                "test_sensitive": test_sensitive,
                "status": (
                    "usable" if test_sensitive else "rejected"
                ),
                "rejection_or_detection_stage": failure_stage,
            }
            hole_results.append(result)
            checkpoint_holes[key] = result
            _write_jsonl(hole_checkpoint, list(checkpoint_holes.values()))

    _write_jsonl(target_checkpoint, list(checkpoint_targets.values()))
    _write_jsonl(hole_checkpoint, list(checkpoint_holes.values()))
    usable = [row for row in hole_results if row["test_sensitive"]]
    granularities_by_target: dict[str, list[str]] = {}
    for row in usable:
        granularities_by_target.setdefault(str(row["target_id"]), []).append(
            str(row["granularity"])
        )
    qualified_targets = []
    for row in rows:
        target_id = str(row["target_id"])
        granularities = granularities_by_target.get(target_id)
        if not granularities:
            continue
        qualified = dict(row)
        qualified["validated_granularities"] = sorted(granularities)
        qualified_targets.append(qualified)
    _write_jsonl(output / "qualified_holes.jsonl", usable)
    _write_jsonl(output / "qualified_targets.jsonl", qualified_targets)
    balanced_targets: list[dict[str, Any]] = []
    balanced_counts: Counter[str] = Counter()
    effective_limit = (
        min(retain_per_language, per_language)
        if per_language is not None
        else retain_per_language
    )
    for row in qualified_targets:
        language = str(row["language"])
        if balanced_counts[language] >= effective_limit:
            continue
        balanced_targets.append(row)
        balanced_counts[language] += 1
    balanced_ids = {str(row["target_id"]) for row in balanced_targets}
    balanced_holes = [row for row in usable if str(row["target_id"]) in balanced_ids]
    _write_jsonl(output / "balanced_targets.jsonl", balanced_targets)
    _write_jsonl(output / "balanced_holes.jsonl", balanced_holes)
    report = {
        "schema_version": 1,
        "experiment": "recent-repository-completion-native-hole-validation",
        "manifest_verification": manifest_verification,
        "selected_target_count": len(rows),
        "baseline_pass_count": sum(row["baseline"]["passed"] for row in target_results),
        "hole_configuration_count": len(hole_results),
        "syntax_valid_count": sum(row["syntax_valid"] for row in hole_results),
        "test_sensitive_count": len(usable),
        "qualified_target_count": len(qualified_targets),
        "qualified_target_count_by_language": {
            language: sum(row["language"] == language for row in qualified_targets)
            for language in ("java", "python")
        },
        "balanced_target_count": len(balanced_targets),
        "balanced_target_count_by_language": dict(balanced_counts),
        "balanced_hole_count": len(balanced_holes),
        "balanced_hole_count_by_granularity": {
            granularity: sum(
                row["granularity"] == granularity for row in balanced_holes
            )
            for granularity in GRANULARITIES
        },
        "test_sensitive_by_language": {
            language: sum(row["language"] == language for row in usable)
            for language in ("java", "python")
        },
        "test_sensitive_by_granularity": {
            granularity: sum(row["granularity"] == granularity for row in usable)
            for granularity in GRANULARITIES
        },
        "status_counts": dict(
            Counter(str(row["rejection_or_detection_stage"]) for row in hole_results)
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that recent method and statement holes are test-sensitive."
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--per-language", type=int)
    parser.add_argument("--retain-per-language", type=int, default=25)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if args.per_language is not None and args.per_language < 1:
        parser.error("--per-language must be positive")
    if args.retain_per_language < 1:
        parser.error("--retain-per-language must be positive")
    workspace = args.workspace.resolve()
    manifest = args.manifest or (
        workspace
        / "data/experiments/recent-repository-completion/candidate_manifest.jsonl"
    )
    output = args.output or (
        workspace / "data/experiments/recent-repository-completion/native-validation"
    )
    report = validate(
        workspace=workspace,
        manifest=manifest.resolve(),
        output=output.resolve(),
        timeout_seconds=args.timeout_seconds,
        per_language=args.per_language,
        retain_per_language=args.retain_per_language,
        replace=args.replace,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
