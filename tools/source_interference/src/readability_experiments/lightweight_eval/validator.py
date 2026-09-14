"""Compile and execute standalone HumanEvalPack repair tasks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from readability_data.java_degradation.interferences.core.java import tree, walk
from readability_experiments.benchmark_eval.external_validation import (
    _patch_strip_level,
    normalize_unified_diff,
    patch_paths,
    source_from_benchmark_prompt,
)

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")


def recount_diff_hunks(patch: str) -> str:
    """Correct model-supplied hunk counts without changing patch content."""
    lines = patch.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        match = _HUNK_HEADER.match(lines[index])
        if match is None:
            output.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not lines[end].startswith(
            ("@@ ", "diff --git ", "--- ")
        ):
            end += 1
        body = lines[index + 1 : end]
        old_count = sum(
            line.startswith((" ", "-")) and not line.startswith("--- ") for line in body
        )
        new_count = sum(
            line.startswith((" ", "+")) and not line.startswith("+++ ") for line in body
        )
        output.append(
            f"@@ -{match.group(1)},{old_count} +{match.group(2)},{new_count} @@{match.group(3)}"
        )
        output.extend(body)
        index = end
    return "\n".join(output) + ("\n" if output else "")


def completion_source(answer: str, prefix: str, language: str) -> str:
    """Normalize chat output, then apply official completion semantics."""
    fenced = re.findall(r"```(?:java|python)?\s*\n(.*?)```", answer, re.DOTALL)
    if fenced:
        if language == "python":
            target = re.search(r"(?m)^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", prefix)
            full_pattern = (
                rf"(?m)^(?:async\s+)?def\s+{re.escape(target.group(1))}\s*\("
                if target
                else r"(?m)^(?:async\s+)?def\s+\w+\s*\("
            )
        else:
            full_pattern = r"(?m)^\s*(?:public\s+)?class\s+Solution\b"
        value = next(
            (block for block in reversed(fenced) if re.search(full_pattern, block)),
            fenced[-1],
        ).rstrip()
    else:
        value = answer.rstrip()
    if language == "python" and re.search(r"(?m)^(?:async\s+)?def\s+\w+\s*\(", value):
        return value + "\n"
    if language == "java" and re.search(
        r"(?m)^\s*(?:public\s+)?class\s+Solution\b", value
    ):
        imports = (
            prefix[: prefix.find("class Solution")]
            if "class Solution" in prefix
            else ""
        )
        encoded = value.encode("utf-8")
        solution_classes = []
        for node in walk(tree(encoded).root_node):
            if node.type != "class_declaration":
                continue
            name = node.child_by_field_name("name")
            if (
                name is not None
                and encoded[name.start_byte : name.end_byte] == b"Solution"
            ):
                solution_classes.append(node)
        if len(solution_classes) == 1:
            # Chat models sometimes repeat HumanEvalPack's public Main test
            # harness together with the requested Solution. Keep the source
            # only through Solution so execute_source can append the canonical
            # harness exactly once.
            value = encoded[: solution_classes[0].end_byte].decode("utf-8").rstrip()
        if imports and not re.search(r"(?m)^\s*import\s+", value):
            value = imports + value
        return value + "\n"
    if value and not value.startswith(("\n", "\r")):
        value = "\n" + value
    return prefix.rstrip() + value + "\n"


class LightweightPatchValidator:
    """Evaluate one target-only patch with the task's standalone official tests."""

    def __init__(self, run_directory: Path, *, timeout_seconds: float = 30.0) -> None:
        self.run_directory = run_directory.resolve()
        self.timeout_seconds = timeout_seconds
        self.log_root = self.run_directory / "evaluation-logs"
        self.log_root.mkdir(parents=True, exist_ok=True)

    def _run(
        self, command: tuple[str, ...], cwd: Path, logs: list[str]
    ) -> subprocess.CompletedProcess[str]:
        logs.append(f"$ {' '.join(command)}")
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            stdout = (
                error.stdout.decode(errors="replace")
                if isinstance(error.stdout, bytes)
                else (error.stdout or "")
            )
            stderr = (
                error.stderr.decode(errors="replace")
                if isinstance(error.stderr, bytes)
                else (error.stderr or "")
            )
            stderr += f"\nprocess timed out after {self.timeout_seconds:g} seconds\n"
            completed = subprocess.CompletedProcess(command, 124, stdout, stderr)
        logs.extend(
            (completed.stdout, completed.stderr, f"exit_code={completed.returncode}")
        )
        return completed

    def execute_source(self, task: dict[str, Any], source: str) -> dict[str, Any]:
        """Return compile and test outcomes for one complete source variant."""
        language = str(task["language"])
        logs: list[str] = []
        with tempfile.TemporaryDirectory(prefix="readability-light-") as temporary:
            root = Path(temporary)
            if language == "java":
                # HumanEvalPack's Java harness is designed to share the imports
                # at the top of the solution with its public Main test class.
                (root / "Main.java").write_text(
                    source + "\n" + str(task["test_code"]) + "\n", encoding="utf-8"
                )
                compiled = self._run(
                    ("javac", "-encoding", "UTF-8", "Main.java"), root, logs
                )
                tested = (
                    self._run(("java", "-cp", str(root), "Main"), root, logs)
                    if compiled.returncode == 0
                    else None
                )
            elif language == "python":
                (root / "solution.py").write_text(source, encoding="utf-8")
                (root / "runner.py").write_text(
                    source + "\n" + str(task["test_code"]) + "\n", encoding="utf-8"
                )
                compiled = self._run(
                    (sys.executable, "-m", "py_compile", "solution.py"), root, logs
                )
                tested = (
                    self._run((sys.executable, "-I", "runner.py"), root, logs)
                    if compiled.returncode == 0
                    else None
                )
            else:
                raise ValueError(f"unsupported lightweight language: {language}")
        return {
            "compiled": compiled.returncode == 0,
            "tests_passed": tested is not None and tested.returncode == 0,
            "compile_timed_out": compiled.returncode == 124,
            "test_timed_out": tested is not None and tested.returncode == 124,
            "compile_exit_code": compiled.returncode,
            "test_exit_code": tested.returncode if tested is not None else None,
            "log_text": "\n".join(logs) + "\n",
        }

    def validate(self, task: dict[str, Any], answer: str, model: str) -> dict[str, Any]:
        started = time.monotonic()
        result: dict[str, Any] = {
            "task_id": task.get("task_id"),
            "model": model,
            "benchmark": "humanevalpack",
            "base_task_id": task.get("base_task_id"),
            "correct": False,
            "functional_success": False,
            "patch_applied": False,
            "compiled": None,
            "trigger_tests_passed": None,
            "regression_tests_passed": None,
            "status": "invalid_patch",
        }
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{task.get('task_id')}--{model}")
        log_path = self.log_root / f"{safe}.log"
        logs: list[str] = []
        try:
            if task.get("expected_kind") == "lightweight_completion_validation":
                source = completion_source(
                    answer,
                    str(task["completion_prefix"]),
                    str(task["language"]),
                )
                execution = self.execute_source(task, source)
                logs.append(execution.pop("log_text"))
                success = bool(execution["compiled"] and execution["tests_passed"])
                result.update(
                    correct=success,
                    functional_success=success,
                    patch_applied=None,
                    compiled=execution["compiled"],
                    trigger_tests_passed=execution["tests_passed"],
                    regression_tests_passed=execution["tests_passed"],
                    status="passed"
                    if success
                    else (
                        "tests_failed" if execution["compiled"] else "compile_failed"
                    ),
                    output_format="official_code_completion",
                    execution=execution,
                )
                return result
            patch = recount_diff_hunks(normalize_unified_diff(answer))
            target = str(task["source_path"])
            paths = patch_paths(patch)
            result.update(patch_paths=sorted(paths), target_path=target)
            if not patch or paths != {target}:
                result["status"] = "invalid_patch_scope"
                return result
            with tempfile.TemporaryDirectory(
                prefix="readability-light-patch-"
            ) as temporary:
                root = Path(temporary)
                target_path = root / target
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(
                    source_from_benchmark_prompt(str(task["prompt"])), encoding="utf-8"
                )
                patch_file = root / "model.patch"
                patch_file.write_text(patch, encoding="utf-8")
                applied = self._run(
                    (
                        "git",
                        "apply",
                        "--no-index",
                        "--recount",
                        f"-p{_patch_strip_level(patch)}",
                        "--whitespace=nowarn",
                        str(patch_file),
                    ),
                    root,
                    logs,
                )
                if applied.returncode != 0:
                    # LLMs often identify the exact edit but emit stale hunk
                    # line numbers. BSD patch can relocate an otherwise valid
                    # hunk by its source context; scope remains target-only.
                    target_path.write_text(
                        source_from_benchmark_prompt(str(task["prompt"])),
                        encoding="utf-8",
                    )
                    applied = self._run(
                        (
                            "patch",
                            "--batch",
                            "--forward",
                            f"-p{_patch_strip_level(patch)}",
                            "-F",
                            "3",
                            "-i",
                            str(patch_file),
                        ),
                        root,
                        logs,
                    )
                    if applied.returncode != 0:
                        result["status"] = "patch_apply_failed"
                        return result
                result["patch_applied"] = True
                execution = self.execute_source(
                    task, target_path.read_text(encoding="utf-8")
                )
                logs.append(execution.pop("log_text"))
                success = bool(execution["compiled"] and execution["tests_passed"])
                result.update(
                    correct=success,
                    functional_success=success,
                    compiled=execution["compiled"],
                    trigger_tests_passed=execution["tests_passed"],
                    regression_tests_passed=execution["tests_passed"],
                    status="passed"
                    if success
                    else (
                        "tests_failed" if execution["compiled"] else "compile_failed"
                    ),
                    execution=execution,
                )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            result.update(
                correct=None,
                functional_success=None,
                status="infrastructure_error",
                error_type=type(error).__name__,
                error=str(error),
            )
        finally:
            result["duration_seconds"] = round(time.monotonic() - started, 3)
            result["log"] = log_path.relative_to(self.run_directory).as_posix()
            log_path.write_text("\n".join(logs), encoding="utf-8")
        return result


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)
