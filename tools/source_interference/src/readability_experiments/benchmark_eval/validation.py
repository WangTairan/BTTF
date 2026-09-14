"""Validate readability interferences against real buggy and fixed revisions."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext

from .class_source import transform_java_class, transform_python_class


@dataclass(frozen=True)
class PreparedInstance:
    instance_id: str
    language: str
    class_name: str
    source_path: Path
    buggy_root: Path
    fixed_root: Path
    test_command: tuple[str, ...]
    environment: dict[str, str]
    expected_failure_markers: tuple[str, ...] = ()


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _run(
    root: Path, command: tuple[str, ...], environment: dict[str, str], timeout: int
) -> dict[str, object]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env={**os.environ, **environment},
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = completed.stdout + completed.stderr
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output": output,
        }
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode()
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        stderr = (
            error.stderr.decode()
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        return {
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output": stdout + stderr,
        }


def _transform(
    language: str,
    source: bytes,
    class_name: str,
    plugin: object,
    context: InterferenceContext,
) -> tuple[bytes, dict[str, int]]:
    if language == "java":
        stats: dict[str, int] = {}

        def apply_java(unit: bytes) -> bytes:
            result = plugin.apply(unit, context)  # type: ignore[attr-defined]
            stats.update(result.stats)
            return result.content

        return transform_java_class(source, class_name, apply_java), stats
    if language == "python":
        text = source.decode("utf-8")
        stats = {}

        def apply_python(unit: str) -> str:
            result = plugin.apply(unit, context)  # type: ignore[attr-defined]
            stats.update(result.stats)
            return result.content

        return transform_python_class(text, class_name, apply_python).encode(
            "utf-8"
        ), stats
    raise ValueError(f"unsupported language: {language}")


def validate_prepared_instance(
    instance: PreparedInstance,
    output: Path,
    seed: int = 20260823,
    timeout: int = 180,
) -> dict[str, object]:
    """Validate one prepared benchmark instance against every language plugin."""
    plugins = (
        JAVA_INTERFERENCES if instance.language == "java" else PYTHON_INTERFERENCES
    )
    buggy_path = instance.buggy_root / instance.source_path
    fixed_path = instance.fixed_root / instance.source_path
    buggy_original = buggy_path.read_bytes()
    fixed_original = fixed_path.read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []

    def execute(label: str, root: Path) -> dict[str, object]:
        result = _run(root, instance.test_command, instance.environment, timeout)
        log_path = output / "logs" / f"{label}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(str(result.pop("output")), encoding="utf-8")
        result["log_path"] = log_path.relative_to(output).as_posix()
        return result

    baseline_buggy = execute("original-buggy", instance.buggy_root)
    baseline_fixed = execute("original-fixed", instance.fixed_root)
    baseline_valid = (
        baseline_buggy["exit_code"] != 0 and baseline_fixed["exit_code"] == 0
    )
    if not baseline_valid:
        raise RuntimeError(f"baseline behavior is invalid for {instance.instance_id}")

    try:
        for order, plugin in enumerate(plugins, start=1):
            slug = str(plugin.slug)
            identity = (
                f"{instance.instance_id}:{instance.source_path}:{instance.class_name}"
            )
            context = InterferenceContext(seed, identity)
            record: dict[str, object] = {
                "schema_version": 1,
                "instance_id": instance.instance_id,
                "language": instance.language,
                "class_name": instance.class_name,
                "source_path": instance.source_path.as_posix(),
                "order": order,
                "category": str(plugin.category),
                "interference": slug,
            }
            try:
                buggy_variant, buggy_stats = _transform(
                    instance.language,
                    buggy_original,
                    instance.class_name,
                    plugin,
                    context,
                )
                fixed_variant, fixed_stats = _transform(
                    instance.language,
                    fixed_original,
                    instance.class_name,
                    plugin,
                    context,
                )
                changed = buggy_variant != buggy_original
                record.update(
                    {
                        "changed": changed,
                        "buggy_stats": buggy_stats,
                        "fixed_stats": fixed_stats,
                        "buggy_source_sha256": _digest(buggy_variant),
                        "fixed_source_sha256": _digest(fixed_variant),
                    }
                )
                variant_dir = output / "variants" / f"I{order:02d}-{slug}"
                variant_dir.mkdir(parents=True, exist_ok=True)
                suffix = instance.source_path.suffix
                (variant_dir / f"buggy{suffix}").write_bytes(buggy_variant)
                (variant_dir / f"fixed{suffix}").write_bytes(fixed_variant)
                if not changed:
                    record["status"] = "not_applicable"
                    records.append(record)
                    continue
                buggy_path.write_bytes(buggy_variant)
                fixed_path.write_bytes(fixed_variant)
                buggy_result = execute(
                    f"I{order:02d}-{slug}-buggy", instance.buggy_root
                )
                fixed_result = execute(
                    f"I{order:02d}-{slug}-fixed", instance.fixed_root
                )
                markers_preserved = all(
                    marker
                    in (output / str(buggy_result["log_path"])).read_text(
                        encoding="utf-8"
                    )
                    for marker in instance.expected_failure_markers
                )
                semantic_valid = (
                    buggy_result["exit_code"] != 0
                    and not buggy_result["timed_out"]
                    and fixed_result["exit_code"] == 0
                    and not fixed_result["timed_out"]
                    and markers_preserved
                )
                record.update(
                    {
                        "status": "valid" if semantic_valid else "rejected",
                        "semantic_valid": semantic_valid,
                        "failure_markers_preserved": markers_preserved,
                        "buggy_test": buggy_result,
                        "fixed_test": fixed_result,
                    }
                )
            except Exception as error:
                record.update(
                    {
                        "status": "transform_error",
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
            finally:
                buggy_path.write_bytes(buggy_original)
                fixed_path.write_bytes(fixed_original)
            records.append(record)
    finally:
        buggy_path.write_bytes(buggy_original)
        fixed_path.write_bytes(fixed_original)

    with (output / "validation.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    counts = Counter(str(record["status"]) for record in records)
    report: dict[str, object] = {
        "schema_version": 1,
        "instance_id": instance.instance_id,
        "language": instance.language,
        "source_path": instance.source_path.as_posix(),
        "class_name": instance.class_name,
        "seed": seed,
        "interference_count": len(records),
        "status_counts": dict(sorted(counts.items())),
        "valid_condition_count_including_original": 1 + counts["valid"],
        "baseline": {"buggy": baseline_buggy, "fixed": baseline_fixed},
        "source_hashes": {
            "buggy": _digest(buggy_original),
            "fixed": _digest(fixed_original),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
