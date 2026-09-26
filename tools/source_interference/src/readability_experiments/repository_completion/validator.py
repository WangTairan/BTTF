"""Validate a model-produced repository span against hidden native tests."""

from __future__ import annotations

import ast
import hashlib
import re
import textwrap
import time
from pathlib import Path
from typing import Any

from readability_experiments.common.paths import default_workspace

from .builder import _run_test, source_with_completion
from .catalog import REPOSITORIES


def normalize_completion(answer: str, language: str) -> str:
    """Accept a bare span or one fenced span; reject empty model output."""
    fenced = re.findall(
        r"```(?:python|py|java)?\s*\n(.*?)```", answer, flags=re.DOTALL | re.IGNORECASE
    )
    value = fenced[-1] if fenced else answer
    value = textwrap.dedent(value).strip("\r\n")
    if not value.strip():
        raise ValueError("model returned an empty completion")
    return value


def _command(
    task: dict[str, Any], *, repository: Path, workspace: Path
) -> list[str]:
    return [
        str(part)
        .replace("${WORKSPACE}", str(workspace))
        .replace("${REPOSITORY}", str(repository))
        for part in task["test_command"]
    ]


class RepositoryCompletionValidator:
    def __init__(
        self,
        run_directory: Path,
        *,
        workspace: Path | None = None,
        timeout_seconds: float = 900.0,
    ) -> None:
        self.workspace = (workspace or default_workspace()).resolve()
        self.run_directory = run_directory.resolve()
        self.timeout_seconds = timeout_seconds
        self.log_root = self.run_directory / "evaluation-logs"
        self.log_root.mkdir(parents=True, exist_ok=True)
        self.specs = {spec.repository_id: spec for spec in REPOSITORIES}

    def validate(
        self, task: dict[str, Any], answer: str, model: str
    ) -> dict[str, Any]:
        started = time.monotonic()
        task_id = str(task["task_id"])
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{task_id}--{model}")
        log_path = self.log_root / f"{safe}.log"
        result: dict[str, Any] = {
            "task_id": task_id,
            "model": model,
            "repository_id": task.get("repository_id"),
            "target_id": task.get("target_id"),
            "granularity": task.get("granularity"),
            "correct": False,
            "functional_success": False,
            "compiled": None,
            "trigger_tests_passed": None,
            "regression_tests_passed": None,
            "status": "invalid_completion",
        }
        logs: list[str] = []
        try:
            repository_id = str(task["repository_id"])
            spec = self.specs[repository_id]
            repository = (
                self.workspace / "data/raw/completion_pilot" / spec.directory
            )
            source_path = repository / str(task["source_path"])
            source = source_path.read_text(encoding="utf-8")
            source_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if source_sha != task["source_sha256"]:
                raise ValueError("pinned source hash does not match the task snapshot")
            source_with_hole = str(task["source_with_hole"])
            prompt_hash = hashlib.sha256(source_with_hole.encode("utf-8")).hexdigest()
            expected_prompt_hash = task.get("prompt_source_sha256")
            if expected_prompt_hash is not None and prompt_hash != expected_prompt_hash:
                raise ValueError("prompt source hash does not match the task snapshot")
            try:
                completion = normalize_completion(answer, str(task["language"]))
            except ValueError as error:
                result.update(status="invalid_completion", error=str(error))
                logs.append(str(error))
                return result
            candidate = source_with_completion(source_with_hole, completion)
            if str(task["language"]) != "python":
                raise ValueError("this validator pilot currently supports Python only")
            try:
                ast.parse(candidate)
            except SyntaxError as error:
                result.update(status="syntax_failed", syntax_error=str(error))
                logs.append(str(error))
                return result
            execution = _run_test(
                repo=repository,
                source_path=source_path,
                candidate=candidate,
                command=_command(task, repository=repository, workspace=self.workspace),
                timeout_seconds=self.timeout_seconds,
            )
            logs.append(execution.pop("output"))
            passed = bool(execution["passed"])
            completion_hash = hashlib.sha256(completion.encode("utf-8")).hexdigest()
            candidate_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
            result.update(
                correct=passed,
                functional_success=passed,
                compiled=True,
                trigger_tests_passed=passed,
                status="passed" if passed else "tests_failed",
                normalized_completion=completion,
                completion_sha256=completion_hash,
                exact_gold_match=candidate_hash
                == task.get("gold_source_sha256", task["source_sha256"]),
                candidate_source_sha256=candidate_hash,
                execution=execution,
            )
            return result
        finally:
            result["duration_seconds"] = round(time.monotonic() - started, 3)
            result["log"] = log_path.relative_to(self.run_directory).as_posix()
            log_path.write_text("\n".join(logs).rstrip() + "\n", encoding="utf-8")
