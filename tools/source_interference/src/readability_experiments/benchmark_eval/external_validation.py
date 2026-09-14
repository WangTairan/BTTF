"""Execute model-generated repair patches against their benchmark tests."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

_BUGGY_SOURCE = re.compile(
    r"\n(?:Buggy source|Source code):\n\n```(?:java|python)?\n(.*?)\n```\n\nRelevant failing test(?: code)?s?:",
    re.DOTALL,
)
_DIFF_PATH = re.compile(r"^(?:---|\+\+\+)\s+(?:[ab]/)?([^\t\n]+)", re.MULTILINE)
_FAILING_TESTS = re.compile(r"Failing tests:\s*(\d+)")
_PYTEST_FAILED = re.compile(r"^FAILED\s+(\S+)", re.MULTILINE)


def _defects4j_failure_ids(checkout: Path) -> list[str]:
    path = checkout / "failing_tests"
    if not path.is_file():
        return []
    return [
        line[4:].strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("--- ")
    ]


def _pytest_failure_ids(output: str) -> list[str]:
    return sorted(set(_PYTEST_FAILED.findall(output)))


def normalize_unified_diff(answer: str) -> str:
    """Remove a single Markdown fence while leaving the unified diff intact."""
    value = answer.strip()
    if value.startswith("```"):
        first_newline = value.find("\n")
        if first_newline >= 0:
            value = value[first_newline + 1 :].rstrip()
    if value.endswith("```"):
        value = value[:-3].rstrip()
    return value + ("\n" if value else "")


def source_from_benchmark_prompt(prompt: str) -> str:
    """Return the exact source variant supplied to the model."""
    match = _BUGGY_SOURCE.search(prompt)
    if match is None:
        raise ValueError(
            "benchmark prompt does not contain a delimited buggy source file"
        )
    return match.group(1)


def patch_paths(patch: str) -> set[str]:
    paths = set()
    for match in _DIFF_PATH.finditer(patch):
        path = match.group(1).strip()
        if path != "/dev/null":
            paths.add(path)
    return paths


def _patch_strip_level(patch: str) -> int:
    headers = [
        line.split(maxsplit=1)[1].split("\t", 1)[0]
        for line in patch.splitlines()
        if (line.startswith("--- ") or line.startswith("+++ "))
        and "/dev/null" not in line
    ]
    return (
        1 if headers and all(value.startswith(("a/", "b/")) for value in headers) else 0
    )


def _catalog(path: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["instance_id"]): row
        for row in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def _java_home() -> str | None:
    configured = os.environ.get("JAVA_HOME")
    if configured:
        release = Path(configured) / "release"
        if release.is_file() and re.search(
            r'^JAVA_VERSION="11(?:[.\"])+',
            release.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            return configured
    executable = shutil.which("java")
    if executable:
        home = Path(executable).resolve().parent.parent
        release = home / "release"
        if release.is_file() and re.search(
            r'^JAVA_VERSION="11(?:[.\"])+',
            release.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            return str(home)
    return None


class ExternalPatchValidator:
    """Benchmark-specific dynamic evaluator with auditable per-response logs."""

    def __init__(
        self,
        workspace: Path,
        run_directory: Path,
        *,
        timeout_seconds: float = 900.0,
        run_regression_tests: bool = True,
    ) -> None:
        self.workspace = workspace.resolve()
        self.run_directory = run_directory.resolve()
        self.timeout_seconds = timeout_seconds
        self.run_regression_tests = run_regression_tests
        catalog_root = self.workspace / "data/benchmarks/catalogs/repair-benchmarks"
        self.catalogs = {
            "defects4j": _catalog(catalog_root / "defects4j.jsonl"),
            "bugsinpy": _catalog(catalog_root / "bugsinpy.jsonl"),
        }
        self.log_root = self.run_directory / "evaluation-logs"
        self.log_root.mkdir(parents=True, exist_ok=True)

    def validate(self, task: dict[str, Any], answer: str, model: str) -> dict[str, Any]:
        started = time.monotonic()
        benchmark = str(task.get("benchmark"))
        identity = str(task.get("base_task_id"))
        result: dict[str, Any] = {
            "task_id": task.get("task_id"),
            "model": model,
            "benchmark": benchmark,
            "base_task_id": identity,
            "correct": None,
            "functional_success": None,
            "patch_applied": False,
            "compiled": None,
            "trigger_tests_passed": None,
            "regression_tests_passed": None,
            "status": "infrastructure_error",
        }
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{task.get('task_id')}--{model}")
        log_path = self.log_root / f"{safe_name}.log"
        logs: list[str] = []
        try:
            record = self.catalogs[benchmark][identity]
            if benchmark == "defects4j":
                result.update(self._validate_defects4j(task, record, answer, logs))
            elif benchmark == "bugsinpy":
                result.update(self._validate_bugsinpy(task, record, answer, logs))
            else:
                raise ValueError(f"unsupported benchmark: {benchmark}")
        except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
            result.update(error_type=type(error).__name__, error=str(error))
        finally:
            result["duration_seconds"] = round(time.monotonic() - started, 3)
            result["log"] = log_path.relative_to(self.run_directory).as_posix()
            log_path.write_text(
                "\n".join(logs) + ("\n" if logs else ""), encoding="utf-8"
            )
        return result

    def probe_buggy_source(self, task: dict[str, Any]) -> dict[str, Any]:
        """Compile and run released trigger tests on the exact prompted source.

        This is used before any model call.  A usable repair input must compile
        and must still exhibit the benchmark defect under its released tests.
        """
        benchmark = str(task.get("benchmark"))
        identity = str(task.get("base_task_id"))
        record = self.catalogs[benchmark][identity]
        logs: list[str] = []
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(task.get("task_id")))
        log_path = self.log_root / f"{safe_name}--prevalidation-buggy.log"
        started = time.monotonic()
        try:
            if benchmark == "defects4j":
                result = self._probe_defects4j(task, record, logs)
            elif benchmark == "bugsinpy":
                result = self._probe_bugsinpy(task, record, logs)
            else:
                raise ValueError(f"unsupported benchmark: {benchmark}")
        except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
            result = {
                "status": "infrastructure_error",
                "compiled": None,
                "trigger_failure_preserved": None,
                "error_type": type(error).__name__,
                "error": str(error),
            }
        result.update(
            duration_seconds=round(time.monotonic() - started, 3),
            log=log_path.relative_to(self.run_directory).as_posix(),
        )
        log_path.write_text("\n".join(logs) + ("\n" if logs else ""), encoding="utf-8")
        return result

    def probe_fixed_source(self, task: dict[str, Any], source: str) -> dict[str, Any]:
        """Validate a fixed-side source variant in the official fixed revision."""
        benchmark = str(task.get("benchmark"))
        identity = str(task.get("base_task_id"))
        record = self.catalogs[benchmark][identity]
        logs: list[str] = []
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(task.get("task_id")))
        log_path = self.log_root / f"{safe_name}--prevalidation-fixed.log"
        started = time.monotonic()
        try:
            if benchmark == "defects4j":
                result = self._probe_fixed_defects4j(task, record, source, logs)
            elif benchmark == "bugsinpy":
                result = self._probe_fixed_bugsinpy(task, record, source, logs)
            else:
                raise ValueError(f"unsupported benchmark: {benchmark}")
        except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
            result = {
                "status": "infrastructure_error",
                "compiled": None,
                "trigger_tests_passed": None,
                "regression_tests_passed": None,
                "functional_success": None,
                "error_type": type(error).__name__,
                "error": str(error),
            }
        result.update(
            duration_seconds=round(time.monotonic() - started, 3),
            log=log_path.relative_to(self.run_directory).as_posix(),
        )
        log_path.write_text("\n".join(logs) + ("\n" if logs else ""), encoding="utf-8")
        return result

    def _defects4j_environment(self, framework: Path) -> dict[str, str]:
        env = os.environ.copy()
        perl_lib = framework / "perl5/lib/perl5"
        env["PERL5LIB"] = (
            f"{perl_lib}:{env['PERL5LIB']}" if env.get("PERL5LIB") else str(perl_lib)
        )
        java_home = _java_home()
        if java_home:
            env["JAVA_HOME"] = java_home
            env["PATH"] = f"{java_home}/bin:{env.get('PATH', '')}"
        return env

    def _probe_fixed_defects4j(
        self, task: dict[str, Any], record: dict[str, Any], source: str, logs: list[str]
    ) -> dict[str, Any]:
        framework = self.workspace / "data/benchmarks/frameworks/defects4j"
        executable = framework / "framework/bin/defects4j"
        if not executable.is_file() or not (framework / "major").is_dir():
            raise FileNotFoundError(
                "Defects4J is not initialized; run its init.sh first"
            )
        triggers = [str(value) for value in record.get("trigger_tests", [])]
        if not triggers:
            raise ValueError("Defects4J task has no triggering tests")
        env = self._defects4j_environment(framework)
        with tempfile.TemporaryDirectory(prefix="readability-d4j-fixed-") as temporary:
            checkout = Path(temporary) / "checkout"
            checked_out = self._run(
                (
                    str(executable),
                    "checkout",
                    "-p",
                    str(task["project"]),
                    "-v",
                    f"{task['bug_id']}f",
                    "-w",
                    str(checkout),
                ),
                cwd=framework,
                env=env,
                logs=logs,
            )
            if checked_out.returncode != 0:
                return {"status": "checkout_failed", "functional_success": None}
            (checkout / str(task["source_path"])).write_text(source, encoding="utf-8")
            compiled = self._run(
                (str(executable), "compile"), cwd=checkout, env=env, logs=logs
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "compiled": False,
                    "functional_success": False,
                }
            trigger_results = []
            triggers_passed = True
            for trigger in triggers:
                tested = self._run(
                    (str(executable), "test", "-t", trigger),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                passed = tested.returncode == 0 and bool(counts) and counts[-1] == 0
                trigger_results.append(
                    {
                        "test": trigger,
                        "failing_tests": counts[-1] if counts else None,
                        "passed": passed,
                    }
                )
                triggers_passed = triggers_passed and passed
            regression_passed: bool | None = None
            if triggers_passed and self.run_regression_tests:
                tested = self._run(
                    (str(executable), "test"), cwd=checkout, env=env, logs=logs
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                regression_passed = (
                    tested.returncode == 0 and bool(counts) and counts[-1] == 0
                )
            success = triggers_passed and (
                regression_passed is True if self.run_regression_tests else True
            )
            return {
                "status": "passed"
                if success
                else (
                    "regression_tests_failed"
                    if triggers_passed
                    else "trigger_tests_failed"
                ),
                "compiled": True,
                "trigger_tests_passed": triggers_passed,
                "regression_tests_passed": regression_passed,
                "functional_success": success,
                "trigger_tests": trigger_results,
            }

    def _probe_fixed_bugsinpy(
        self, task: dict[str, Any], record: dict[str, Any], source: str, logs: list[str]
    ) -> dict[str, Any]:
        instance_id = str(task["base_task_id"])
        prepared = self.workspace / "data/benchmarks/worktrees" / instance_id / "fixed"
        if not prepared.is_dir():
            raise FileNotFoundError(
                f"no prepared fixed BugsInPy checkout for {instance_id}; expected {prepared}"
            )
        python = self._bugsinpy_python(task, record)
        commands = [str(value) for value in record.get("test_commands", [])]
        if not commands:
            raise ValueError("BugsInPy task has no released test command")
        env = os.environ.copy()
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"})
        with tempfile.TemporaryDirectory(prefix="readability-bip-fixed-") as temporary:
            checkout = Path(temporary) / "checkout"
            shutil.copytree(
                prepared,
                checkout,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git", ".pytest_cache", "__pycache__", "*.pyc", "env"
                ),
            )
            target = str(task["source_path"])
            (checkout / target).write_text(source, encoding="utf-8")
            compiled = self._run(
                (str(python), "-m", "py_compile", target),
                cwd=checkout,
                env=env,
                logs=logs,
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "compiled": False,
                    "functional_success": False,
                }
            trigger_results = []
            triggers_passed = True
            for released in commands:
                for command in self._bugsinpy_test_commands(released, python):
                    tested = self._run(command, cwd=checkout, env=env, logs=logs)
                    passed = tested.returncode == 0
                    trigger_results.append(
                        {
                            "command": shlex.join(command),
                            "released_command": released,
                            "passed": passed,
                        }
                    )
                    triggers_passed = triggers_passed and passed
            regression_passed: bool | None = None
            if triggers_passed and self.run_regression_tests:
                if not any("pytest" in shlex.split(command) for command in commands):
                    return {
                        "status": "regression_unsupported",
                        "compiled": True,
                        "trigger_tests_passed": True,
                        "regression_tests_passed": None,
                        "functional_success": None,
                        "trigger_tests": trigger_results,
                    }
                tested = self._run(
                    (str(python), "-m", "pytest", "-q"),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                regression_passed = tested.returncode == 0
            success = triggers_passed and (
                regression_passed is True if self.run_regression_tests else True
            )
            return {
                "status": "passed"
                if success
                else (
                    "regression_tests_failed"
                    if triggers_passed
                    else "trigger_tests_failed"
                ),
                "compiled": True,
                "trigger_tests_passed": triggers_passed,
                "regression_tests_passed": regression_passed,
                "functional_success": success,
                "trigger_tests": trigger_results,
            }

    def _probe_defects4j(
        self, task: dict[str, Any], record: dict[str, Any], logs: list[str]
    ) -> dict[str, Any]:
        framework = self.workspace / "data/benchmarks/frameworks/defects4j"
        executable = framework / "framework/bin/defects4j"
        if not executable.is_file() or not (framework / "major").is_dir():
            raise FileNotFoundError(
                "Defects4J is not initialized; run its init.sh first"
            )
        env = self._defects4j_environment(framework)
        triggers = [str(value) for value in record.get("trigger_tests", [])]
        if not triggers:
            raise ValueError("Defects4J task has no triggering tests")
        with tempfile.TemporaryDirectory(prefix="readability-d4j-probe-") as temporary:
            checkout = Path(temporary) / "checkout"
            checked_out = self._run(
                (
                    str(executable),
                    "checkout",
                    "-p",
                    str(task["project"]),
                    "-v",
                    f"{task['bug_id']}b",
                    "-w",
                    str(checkout),
                ),
                cwd=framework,
                env=env,
                logs=logs,
            )
            if checked_out.returncode != 0:
                return {
                    "status": "checkout_failed",
                    "compiled": None,
                    "trigger_failure_preserved": None,
                }
            target_path = checkout / str(task["source_path"])
            target_path.write_text(
                source_from_benchmark_prompt(str(task["prompt"])), encoding="utf-8"
            )
            compiled = self._run(
                (str(executable), "compile"), cwd=checkout, env=env, logs=logs
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "compiled": False,
                    "trigger_failure_preserved": None,
                }
            tests = []
            all_failed = True
            for trigger in triggers:
                tested = self._run(
                    (str(executable), "test", "-t", trigger),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                failed = bool(counts) and counts[-1] > 0
                tests.append(
                    {
                        "test": trigger,
                        "failing_tests": counts[-1] if counts else None,
                        "failed": failed,
                    }
                )
                all_failed = all_failed and failed
            regression_failure_ids: list[str] | None = None
            regression_failure_count: int | None = None
            if all_failed and self.run_regression_tests:
                tested = self._run(
                    (str(executable), "test"), cwd=checkout, env=env, logs=logs
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                regression_failure_ids = _defects4j_failure_ids(checkout)
                regression_failure_count = counts[-1] if counts else None
            return {
                "status": "expected_failure" if all_failed else "failure_not_preserved",
                "compiled": True,
                "trigger_failure_preserved": all_failed,
                "trigger_tests": tests,
                "regression_failure_ids": regression_failure_ids,
                "regression_failure_count": regression_failure_count,
            }

    def _probe_bugsinpy(
        self, task: dict[str, Any], record: dict[str, Any], logs: list[str]
    ) -> dict[str, Any]:
        instance_id = str(task["base_task_id"])
        prepared = self.workspace / "data/benchmarks/worktrees" / instance_id / "buggy"
        if not prepared.is_dir():
            raise FileNotFoundError(
                f"no prepared BugsInPy checkout for {instance_id}; expected {prepared}"
            )
        python = self._bugsinpy_python(task, record)
        commands = [str(value) for value in record.get("test_commands", [])]
        if not commands:
            raise ValueError("BugsInPy task has no released test command")
        env = os.environ.copy()
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"})
        with tempfile.TemporaryDirectory(prefix="readability-bip-probe-") as temporary:
            checkout = Path(temporary) / "checkout"
            shutil.copytree(
                prepared,
                checkout,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git", ".pytest_cache", "__pycache__", "*.pyc", "env"
                ),
            )
            target = str(task["source_path"])
            (checkout / target).write_text(
                source_from_benchmark_prompt(str(task["prompt"])), encoding="utf-8"
            )
            compiled = self._run(
                (str(python), "-m", "py_compile", target),
                cwd=checkout,
                env=env,
                logs=logs,
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "compiled": False,
                    "trigger_failure_preserved": None,
                }
            tests = []
            all_failed = True
            for released in commands:
                for command in self._bugsinpy_test_commands(released, python):
                    tested = self._run(command, cwd=checkout, env=env, logs=logs)
                    failed = tested.returncode != 0
                    tests.append(
                        {
                            "command": shlex.join(command),
                            "released_command": released,
                            "failed": failed,
                        }
                    )
                    all_failed = all_failed and failed
            regression_failure_ids: list[str] | None = None
            regression_failure_count: int | None = None
            if all_failed and self.run_regression_tests:
                if not any("pytest" in shlex.split(command) for command in commands):
                    return {
                        "status": "regression_unsupported",
                        "compiled": True,
                        "trigger_failure_preserved": True,
                        "regression_failure_ids": None,
                        "regression_failure_count": None,
                        "trigger_tests": tests,
                    }
                tested = self._run(
                    (str(python), "-m", "pytest", "-q"),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                regression_failure_ids = _pytest_failure_ids(
                    tested.stdout + tested.stderr
                )
                if tested.returncode != 0 and not regression_failure_ids:
                    return {
                        "status": "regression_infrastructure_error",
                        "compiled": True,
                        "trigger_failure_preserved": True,
                        "regression_failure_ids": [],
                        "regression_failure_count": None,
                        "trigger_tests": tests,
                    }
                regression_failure_count = len(regression_failure_ids)
            return {
                "status": "expected_failure" if all_failed else "failure_not_preserved",
                "compiled": True,
                "trigger_failure_preserved": all_failed,
                "trigger_tests": tests,
                "regression_failure_ids": regression_failure_ids,
                "regression_failure_count": regression_failure_count,
            }

    def _run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
        env: dict[str, str],
        logs: list[str],
    ) -> subprocess.CompletedProcess[str]:
        logs.append(f"$ {' '.join(command)}")
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )
        logs.extend(
            (completed.stdout, completed.stderr, f"exit_code={completed.returncode}")
        )
        return completed

    def _validate_defects4j(
        self,
        task: dict[str, Any],
        record: dict[str, Any],
        answer: str,
        logs: list[str],
    ) -> dict[str, Any]:
        framework = self.workspace / "data/benchmarks/frameworks/defects4j"
        executable = framework / "framework/bin/defects4j"
        if not executable.is_file() or not (framework / "major").is_dir():
            raise FileNotFoundError(
                "Defects4J is not initialized; run its init.sh first"
            )
        patch = normalize_unified_diff(answer)
        target = str(task["source_path"])
        paths = patch_paths(patch)
        if not patch or paths != {target}:
            return {
                "status": "invalid_patch_scope",
                "correct": False,
                "functional_success": False,
                "patch_paths": sorted(paths),
                "target_path": target,
            }
        source = source_from_benchmark_prompt(str(task["prompt"]))
        triggers = [str(value) for value in record.get("trigger_tests", [])]
        if not triggers:
            raise ValueError("Defects4J task has no triggering tests")
        env = self._defects4j_environment(framework)
        with tempfile.TemporaryDirectory(prefix="readability-d4j-") as temporary:
            checkout = Path(temporary) / "checkout"
            checked_out = self._run(
                (
                    str(executable),
                    "checkout",
                    "-p",
                    str(task["project"]),
                    "-v",
                    f"{task['bug_id']}b",
                    "-w",
                    str(checkout),
                ),
                cwd=framework,
                env=env,
                logs=logs,
            )
            if checked_out.returncode != 0:
                return {"status": "checkout_failed", "correct": None}
            target_path = checkout / target
            if not target_path.is_file():
                raise FileNotFoundError(
                    f"target source file not found after checkout: {target}"
                )
            target_path.write_text(source, encoding="utf-8")
            patch_file = Path(temporary) / "model.patch"
            patch_file.write_text(patch, encoding="utf-8")
            strip_level = _patch_strip_level(patch)
            applied = self._run(
                (
                    "git",
                    "apply",
                    "--recount",
                    f"-p{strip_level}",
                    "--whitespace=nowarn",
                    str(patch_file),
                ),
                cwd=checkout,
                env=env,
                logs=logs,
            )
            if applied.returncode != 0:
                return {
                    "status": "patch_apply_failed",
                    "correct": False,
                    "functional_success": False,
                    "patch_paths": sorted(paths),
                }
            compiled = self._run(
                (str(executable), "compile"), cwd=checkout, env=env, logs=logs
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "correct": False,
                    "functional_success": False,
                    "patch_applied": True,
                    "compiled": False,
                    "patch_paths": sorted(paths),
                }
            test_results = []
            passed = True
            for trigger in triggers:
                tested = self._run(
                    (str(executable), "test", "-t", trigger),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                trigger_passed = (
                    tested.returncode == 0 and bool(counts) and counts[-1] == 0
                )
                test_results.append(
                    {
                        "test": trigger,
                        "exit_code": tested.returncode,
                        "failing_tests": counts[-1] if counts else None,
                        "passed": trigger_passed,
                    }
                )
                passed = passed and trigger_passed
            regression_passed: bool | None = None
            regression: dict[str, Any] | None = None
            if passed and self.run_regression_tests:
                tested = self._run(
                    (str(executable), "test"), cwd=checkout, env=env, logs=logs
                )
                counts = [
                    int(value)
                    for value in _FAILING_TESTS.findall(tested.stdout + tested.stderr)
                ]
                failure_ids = _defects4j_failure_ids(checkout)
                baseline_ids = set(
                    map(str, task.get("regression_baseline_failure_ids", []))
                )
                no_new_failures = (tested.returncode == 0 or bool(failure_ids)) and set(
                    failure_ids
                ).issubset(baseline_ids)
                regression_passed = bool(counts) and no_new_failures
                regression = {
                    "exit_code": tested.returncode,
                    "failing_tests": counts[-1] if counts else None,
                    "passed": regression_passed,
                    "failure_ids": failure_ids,
                    "baseline_failure_ids": sorted(baseline_ids),
                    "no_new_failures": no_new_failures,
                }
            functional_success = passed and (
                regression_passed is True if self.run_regression_tests else True
            )
            return {
                "status": "passed"
                if functional_success
                else ("regression_tests_failed" if passed else "trigger_tests_failed"),
                "correct": functional_success,
                "functional_success": functional_success,
                "patch_applied": True,
                "compiled": True,
                "trigger_tests_passed": passed,
                "regression_tests_passed": regression_passed,
                "patch_paths": sorted(paths),
                "trigger_tests": test_results,
                "regression_tests": regression,
            }

    def _bugsinpy_python(self, task: dict[str, Any], record: dict[str, Any]) -> Path:
        """Resolve a prepared, benchmark-specific interpreter without using user packages."""
        instance_id = str(task["base_task_id"])
        candidates = [
            self.workspace
            / "data/benchmarks/envs/bugsinpy"
            / instance_id
            / "bin/python",
            self.workspace
            / "data/benchmarks/worktrees"
            / instance_id
            / "buggy/env/bin/python",
        ]
        runtime = str(record.get("runtime_version") or "")
        match = re.match(r"(\d+\.\d+)", runtime)
        if match and instance_id == "bugsinpy__PySnooper__2":
            # Compatibility with the first prepared validation environment.
            candidates.append(
                self.workspace
                / "data/benchmarks/envs"
                / f"python-{match.group(1)}"
                / "bin/python"
            )
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise FileNotFoundError(
            f"no prepared BugsInPy environment for {instance_id}; expected {candidates[0]}"
        )

    @staticmethod
    def _bugsinpy_test_command(command: str, python: Path) -> tuple[str, ...]:
        """Bind released test commands to the prepared interpreter."""
        arguments = shlex.split(command)
        if not arguments:
            raise ValueError("empty BugsInPy test command")
        executable = Path(arguments[0]).name
        if executable in {"pytest", "py.test"}:
            return (str(python), "-m", "pytest", *arguments[1:])
        if executable in {"python", "python2", "python3"}:
            return (str(python), *arguments[1:])
        if executable == "tox":
            return (str(python), "-m", "tox", *arguments[1:])
        raise ValueError(f"unsupported BugsInPy test command: {command}")

    @classmethod
    def _bugsinpy_test_commands(
        cls, command: str, python: Path
    ) -> tuple[tuple[str, ...], ...]:
        """Safely expand the one released command that contains two pytest calls."""
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";")
        lexer.whitespace_split = True
        segments: list[list[str]] = [[]]
        for token in lexer:
            if token == ";":
                if not segments[-1]:
                    raise ValueError(f"empty command segment: {command}")
                segments.append([])
            else:
                segments[-1].append(token)
        if not segments[-1]:
            raise ValueError(f"empty command segment: {command}")
        return tuple(
            cls._bugsinpy_test_command(shlex.join(segment), python)
            for segment in segments
        )

    def _validate_bugsinpy(
        self,
        task: dict[str, Any],
        record: dict[str, Any],
        answer: str,
        logs: list[str],
    ) -> dict[str, Any]:
        """Validate one repair in an isolated copy of an official BugsInPy checkout."""
        patch = normalize_unified_diff(answer)
        target = str(task["source_path"])
        paths = patch_paths(patch)
        if not patch or paths != {target}:
            return {
                "status": "invalid_patch_scope",
                "correct": False,
                "functional_success": False,
                "patch_paths": sorted(paths),
                "target_path": target,
            }
        instance_id = str(task["base_task_id"])
        prepared = self.workspace / "data/benchmarks/worktrees" / instance_id / "buggy"
        if not prepared.is_dir():
            raise FileNotFoundError(
                f"no prepared BugsInPy checkout for {instance_id}; expected {prepared}"
            )
        python = self._bugsinpy_python(task, record)
        commands = [str(value) for value in record.get("test_commands", [])]
        if not commands:
            raise ValueError("BugsInPy task has no released test command")
        source = source_from_benchmark_prompt(str(task["prompt"]))
        env = os.environ.copy()
        env.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
            }
        )
        with tempfile.TemporaryDirectory(prefix="readability-bip-") as temporary:
            checkout = Path(temporary) / "checkout"
            shutil.copytree(
                prepared,
                checkout,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git", ".pytest_cache", "__pycache__", "*.pyc", "env"
                ),
            )
            target_path = checkout / target
            if not target_path.is_file():
                raise FileNotFoundError(
                    f"target source file not found in prepared checkout: {target}"
                )
            target_path.write_text(source, encoding="utf-8")
            patch_file = Path(temporary) / "model.patch"
            patch_file.write_text(patch, encoding="utf-8")
            strip_level = _patch_strip_level(patch)
            applied = self._run(
                (
                    "git",
                    "apply",
                    "--no-index",
                    "--recount",
                    f"-p{strip_level}",
                    "--whitespace=nowarn",
                    str(patch_file),
                ),
                cwd=checkout,
                env=env,
                logs=logs,
            )
            if applied.returncode != 0:
                return {
                    "status": "patch_apply_failed",
                    "correct": False,
                    "functional_success": False,
                    "patch_paths": sorted(paths),
                }
            compiled = self._run(
                (str(python), "-m", "py_compile", target),
                cwd=checkout,
                env=env,
                logs=logs,
            )
            if compiled.returncode != 0:
                return {
                    "status": "compile_failed",
                    "correct": False,
                    "functional_success": False,
                    "patch_applied": True,
                    "compiled": False,
                    "patch_paths": sorted(paths),
                }
            test_results = []
            passed = True
            for released in commands:
                for command in self._bugsinpy_test_commands(released, python):
                    tested = self._run(command, cwd=checkout, env=env, logs=logs)
                    command_passed = tested.returncode == 0
                    test_results.append(
                        {
                            "command": shlex.join(command),
                            "released_command": released,
                            "exit_code": tested.returncode,
                            "passed": command_passed,
                        }
                    )
                    passed = passed and command_passed
            regression_passed: bool | None = None
            regression: dict[str, Any] | None = None
            if passed and self.run_regression_tests:
                released_uses_pytest = any(
                    Path(shlex.split(command)[0]).name in {"pytest", "py.test"}
                    or "pytest" in shlex.split(command)
                    for command in commands
                    if shlex.split(command)
                )
                if not released_uses_pytest:
                    return {
                        "status": "regression_unsupported",
                        "correct": None,
                        "functional_success": None,
                        "patch_applied": True,
                        "compiled": True,
                        "trigger_tests_passed": True,
                        "regression_tests_passed": None,
                        "patch_paths": sorted(paths),
                        "trigger_tests": test_results,
                    }
                tested = self._run(
                    (str(python), "-m", "pytest", "-q"),
                    cwd=checkout,
                    env=env,
                    logs=logs,
                )
                failure_ids = _pytest_failure_ids(tested.stdout + tested.stderr)
                baseline_ids = set(
                    map(str, task.get("regression_baseline_failure_ids", []))
                )
                no_new_failures = (tested.returncode == 0 or bool(failure_ids)) and set(
                    failure_ids
                ).issubset(baseline_ids)
                regression_passed = no_new_failures
                regression = {
                    "exit_code": tested.returncode,
                    "passed": regression_passed,
                    "failure_ids": failure_ids,
                    "baseline_failure_ids": sorted(baseline_ids),
                    "no_new_failures": no_new_failures,
                }
            functional_success = passed and (
                regression_passed is True if self.run_regression_tests else True
            )
            return {
                "status": "passed"
                if functional_success
                else ("regression_tests_failed" if passed else "trigger_tests_failed"),
                "correct": functional_success,
                "functional_success": functional_success,
                "patch_applied": True,
                "compiled": True,
                "trigger_tests_passed": passed,
                "regression_tests_passed": regression_passed,
                "patch_paths": sorted(paths),
                "runtime": str(record.get("runtime_version") or ""),
                "python": str(python),
                "trigger_tests": test_results,
                "regression_tests": regression,
            }


def save_evaluation(path: Path, result: dict[str, Any]) -> None:
    """Atomically keep the latest evaluation for each task/model pair."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if path.is_file():
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    key = (result.get("task_id"), result.get("model"))
    rows = [row for row in rows if (row.get("task_id"), row.get("model")) != key]
    rows.append(result)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)
