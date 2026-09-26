"""Build and natively validate paired recent-repository completion tasks."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from readability_data.java_degradation.interferences.core.java import tree, walk
from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext
from readability_experiments.common.paths import default_workspace

from .catalog import PILOT_TARGETS, RepositoryTarget
from .prompts import span_completion_prompt

SEED = 20260823
SENTINEL_NAME = "__READABILITY_HOLE_SENTINEL__"
SENTINEL = SENTINEL_NAME + "()"
HOLE = "<READABILITY_HOLE>"


@dataclass(frozen=True)
class LocatedSpan:
    start: int
    end: int
    indent: str
    completion: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _command(repo: Path, target: RepositoryTarget, workspace: Path) -> list[str]:
    substitutions = {
        "maven_repo": str(workspace / "data/cache/m2"),
        "python": str(repo / ".venv/bin/python"),
    }
    command = [part.format(**substitutions) for part in target.test_args]
    executable = Path(command[0])
    if executable.is_absolute() and not executable.is_file():
        raise FileNotFoundError(
            f"test interpreter is missing for {target.repository_id}: {command[0]}"
        )
    return command


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _verify_repository(repo: Path, target: RepositoryTarget) -> None:
    if not (repo / ".git").is_dir():
        raise FileNotFoundError(f"repository is not prepared: {repo}")
    head = _git(repo, "rev-parse", "HEAD")
    if head != target.pinned_commit:
        raise ValueError(
            f"{target.repository_id} is at {head}; expected {target.pinned_commit}"
        )
    status = _git(repo, "status", "--porcelain", "--untracked-files=no")
    if status:
        raise ValueError(
            f"tracked files are modified in {target.repository_id}:\n{status}"
        )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "merge-base",
            "--is-ancestor",
            target.target_origin_commit,
            target.pinned_commit,
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _line_indent(source: str, offset: int) -> str:
    line_start = source.rfind("\n", 0, offset) + 1
    prefix = source[line_start:offset]
    if prefix.strip():
        raise ValueError("target span does not start after indentation only")
    return prefix


def _replacement_indent(source: str, offset: int) -> str:
    """Return indentation at a hole, or none when layout made it inline."""
    line_start = source.rfind("\n", 0, offset) + 1
    prefix = source[line_start:offset]
    return prefix if not prefix.strip() else ""


def _canonical_completion(raw: str, indent: str) -> str:
    lines = raw.splitlines()
    if not lines:
        raise ValueError("empty target span")
    canonical = [lines[0]]
    for line in lines[1:]:
        if line and not line.startswith(indent):
            raise ValueError("target span has inconsistent indentation")
        canonical.append(line[len(indent) :] if line else "")
    return "\n".join(canonical).rstrip()


def _locate_python(source: str, symbol: str) -> LocatedSpan:
    module = ast.parse(source)
    matches = [
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    ]
    if len(matches) != 1 or not matches[0].body:
        raise ValueError(f"cannot locate unique Python function {symbol!r}")
    node = matches[0]
    first, last = node.body[0], node.body[-1]
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))
    start = starts[first.lineno - 1] + first.col_offset
    end = starts[last.end_lineno - 1] + last.end_col_offset
    encoded = source.encode("utf-8")
    raw = encoded[start:end].decode("utf-8")
    char_start = len(encoded[:start].decode("utf-8"))
    indent = _line_indent(source, char_start)
    return LocatedSpan(start, end, indent, _canonical_completion(raw, indent))


def _locate_java(
    source: str, symbol: str, signature_contains: str | None
) -> LocatedSpan:
    encoded = source.encode("utf-8")
    matches = []
    for node in walk(tree(encoded).root_node):
        if node.type != "method_declaration":
            continue
        name = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if name is None or body is None or not body.named_children:
            continue
        if encoded[name.start_byte : name.end_byte].decode("utf-8") != symbol:
            continue
        signature = encoded[node.start_byte : body.start_byte].decode("utf-8")
        if signature_contains is not None and signature_contains not in signature:
            continue
        matches.append(body)
    if len(matches) != 1:
        raise ValueError(f"cannot locate unique Java method {symbol!r}")
    body = matches[0]
    start = body.named_children[0].start_byte
    end = body.named_children[-1].end_byte
    raw = encoded[start:end].decode("utf-8")
    char_start = len(encoded[:start].decode("utf-8"))
    indent = _line_indent(source, char_start)
    return LocatedSpan(start, end, indent, _canonical_completion(raw, indent))


def locate_span(source: str, target: RepositoryTarget) -> LocatedSpan:
    if target.language == "python":
        return _locate_python(source, target.symbol)
    return _locate_java(source, target.symbol, target.signature_contains)


def _indent_completion(completion: str, indent: str) -> str:
    return completion.replace("\n", "\n" + indent)


def _replace_span(source: str, span: LocatedSpan, replacement: str) -> str:
    encoded = source.encode("utf-8")
    return (
        encoded[: span.start] + replacement.encode("utf-8") + encoded[span.end :]
    ).decode("utf-8")


def _sentinel_source(source: str, span: LocatedSpan, language: str) -> str:
    statement = SENTINEL + (";" if language == "java" else "")
    return _replace_span(source, span, statement)


def _sentinel_statement(source: str) -> str:
    if source.count(SENTINEL) != 1:
        raise ValueError(
            f"expected one completion sentinel, found {source.count(SENTINEL)}"
        )
    java_statement = SENTINEL + ";"
    return java_statement if java_statement in source else SENTINEL


def _replace_sentinel(source: str, replacement: str) -> str:
    statement = _sentinel_statement(source)
    offset = source.index(statement)
    indent = _replacement_indent(source, offset)
    return source.replace(statement, _indent_completion(replacement, indent), 1)


def source_with_hole(sentinel_source: str) -> str:
    return _replace_sentinel(sentinel_source, HOLE)


def source_with_completion(hole_source: str, completion: str) -> str:
    if hole_source.count(HOLE) != 1:
        raise ValueError("source must contain exactly one readability hole")
    offset = hole_source.index(HOLE)
    indent = _replacement_indent(hole_source, offset)
    return hole_source.replace(HOLE, _indent_completion(completion, indent), 1)


def _apply_interference(
    target: RepositoryTarget, source: str, plugin: object
) -> tuple[str, dict[str, int]]:
    context = InterferenceContext(
        seed=SEED,
        identity=(
            f"recent-completion:{target.repository_id}:{target.pinned_commit}:"
            f"{target.source_path}:{target.symbol}"
        ),
        protected_names=(target.symbol, SENTINEL_NAME),
    )
    if target.language == "java":
        result = plugin.apply(  # type: ignore[attr-defined]
            source.encode("utf-8"), context
        )
        return result.content.decode("utf-8"), result.stats
    result = plugin.apply(source, context)  # type: ignore[attr-defined]
    return result.content, result.stats


def _run_test(
    *,
    repo: Path,
    source_path: Path,
    candidate: str,
    command: list[str],
    timeout_seconds: float,
) -> dict[str, Any]:
    original = source_path.read_text(encoding="utf-8")
    started = time.monotonic()
    try:
        source_path.write_text(candidate, encoding="utf-8")
        result = subprocess.run(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"native test timed out after {timeout_seconds:.0f}s: {' '.join(command)}"
        ) from error
    finally:
        source_path.write_text(original, encoding="utf-8")
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output": result.stdout,
    }


def build_target(
    *,
    target: RepositoryTarget,
    repo: Path,
    workspace: Path,
    output: Path,
    timeout_seconds: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _verify_repository(repo, target)
    source_path = repo / target.source_path
    original = source_path.read_text(encoding="utf-8")
    span = locate_span(original, target)
    sentinel_original = _sentinel_source(original, span, target.language)
    build_fingerprint = _sha256(
        json.dumps(asdict(target), sort_keys=True)
        + _sha256(original)
        + str(SEED)
        + "repository-completion-v1"
    )
    plugins = JAVA_INTERFERENCES if target.language == "java" else PYTHON_INTERFERENCES
    candidates: list[tuple[str, str, dict[str, int]]] = [
        ("original", sentinel_original, {})
    ]
    for plugin in plugins:
        transformed, stats = _apply_interference(target, sentinel_original, plugin)
        if transformed == sentinel_original:
            continue
        candidates.append((str(plugin.slug), transformed, stats))

    command = _command(repo, target, workspace)
    test_display = [
        part.replace(str(workspace), "${WORKSPACE}").replace(
            str(repo), "${REPOSITORY}"
        )
        for part in command
    ]
    validation: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    logs = output / "validation-logs"
    logs.mkdir(parents=True, exist_ok=True)
    checkpoint_root = output / "checkpoints"
    validation_checkpoint = checkpoint_root / f"{target.repository_id}.validation.jsonl"
    task_checkpoint = checkpoint_root / f"{target.repository_id}.tasks.jsonl"
    existing_validation = {
        str(row["condition"]): row
        for row in _read_jsonl(validation_checkpoint)
        if row.get("build_fingerprint") == build_fingerprint
    }
    existing_tasks = {
        str(row["condition"]): row
        for row in _read_jsonl(task_checkpoint)
        if row.get("build_fingerprint") == build_fingerprint
    }
    for condition, sentinel_variant, stats in candidates:
        if condition in existing_validation:
            validation.append(existing_validation[condition])
            if condition in existing_tasks:
                tasks.append(existing_tasks[condition])
            print(f"{target.repository_id} {condition}: resumed")
            continue
        print(
            f"{target.repository_id} {condition}: validating gold and hole",
            flush=True,
        )
        gold_source = _replace_sentinel(sentinel_variant, span.completion)
        gold = _run_test(
            repo=repo,
            source_path=source_path,
            candidate=gold_source,
            command=command,
            timeout_seconds=timeout_seconds,
        )
        hole_result = _run_test(
            repo=repo,
            source_path=source_path,
            candidate=sentinel_variant,
            command=command,
            timeout_seconds=timeout_seconds,
        )
        log_base = f"{target.repository_id}--{condition}"
        (logs / f"{log_base}--gold.log").write_text(
            gold.pop("output"), encoding="utf-8"
        )
        (logs / f"{log_base}--hole.log").write_text(
            hole_result.pop("output"), encoding="utf-8"
        )
        usable = bool(gold["passed"] and not hole_result["passed"])
        row = {
            "schema_version": 1,
            "build_fingerprint": build_fingerprint,
            "repository_id": target.repository_id,
            "language": target.language,
            "pinned_commit": target.pinned_commit,
            "target_origin_commit": target.target_origin_commit,
            "target_origin_date": target.target_origin_date,
            "source_path": target.source_path,
            "symbol": target.symbol,
            "condition": condition,
            "interference_stats": stats,
            "context_changed": sentinel_variant != sentinel_original,
            "gold": gold,
            "hole": hole_result,
            "usable": usable,
            "status": "usable" if usable else "rejected",
            "test_command": test_display,
        }
        validation.append(row)
        _write_jsonl(validation_checkpoint, validation)
        if not usable:
            continue
        hole_source = source_with_hole(sentinel_variant)
        task = {
            "schema_version": 1,
            "build_fingerprint": build_fingerprint,
            "task_id": f"recent-completion--{target.repository_id}--{condition}",
            "experiment": "recent-repository-span-completion",
            "expected_kind": "repository_span_completion_validation",
            "prompt_template": "repository-span-completion-v1",
            "repository": asdict(target),
            "condition": condition,
            "interference_seed": SEED,
            "source_with_hole": hole_source,
            "gold_completion": span.completion,
            "gold_source_sha256": _sha256(gold_source),
            "prompt_source_sha256": _sha256(hole_source),
            "test_command": test_display,
            "prompt": span_completion_prompt(
                language=target.language,
                repository=target.repository_id,
                source_path=target.source_path,
                source_with_hole=hole_source,
            ),
        }
        tasks.append(task)
        _write_jsonl(task_checkpoint, tasks)
    _write_jsonl(validation_checkpoint, validation)
    _write_jsonl(task_checkpoint, tasks)
    return validation, tasks


def build_pilot(
    *, workspace: Path, output: Path, timeout_seconds: float
) -> dict[str, Any]:
    validation: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for target in PILOT_TARGETS:
        directory = (
            "commons-collections"
            if target.repository_id == "apache-commons-collections"
            else target.repository_id
        )
        repo = workspace / "data/raw/completion_pilot" / directory
        target_validation, target_tasks = build_target(
            target=target,
            repo=repo,
            workspace=workspace,
            output=output,
            timeout_seconds=timeout_seconds,
        )
        validation.extend(target_validation)
        tasks.extend(target_tasks)
    _write_jsonl(output / "validation.jsonl", validation)
    _write_jsonl(output / "tasks.jsonl", tasks)
    report = {
        "schema_version": 1,
        "experiment": "recent-repository-span-completion-pilot",
        "seed": SEED,
        "target_count": len(PILOT_TARGETS),
        "validated_condition_count": len(validation),
        "usable_task_count": len(tasks),
        "repositories": [asdict(target) for target in PILOT_TARGETS],
        "usable_by_repository": {
            target.repository_id: sum(
                task["repository"]["repository_id"] == target.repository_id
                for task in tasks
            )
            for target in PILOT_TARGETS
        },
        "rejected": [
            {
                "repository_id": row["repository_id"],
                "condition": row["condition"],
                "gold_passed": row["gold"]["passed"],
                "hole_passed": row["hole"]["passed"],
            }
            for row in validation
            if not row["usable"]
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the pinned recent-repository span-completion pilot."
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    output = args.output or (
        workspace / "data/experiments/recent-repository-completion/pilot"
    )
    report = build_pilot(
        workspace=workspace,
        output=output.resolve(),
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
