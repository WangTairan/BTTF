from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .prompts import behavior_prediction_prompt, test_guided_repair_prompt

CASE_INSENSITIVE_HARNESS = """from requests.structures import CaseInsensitiveDict

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["aCCEPT"] = "text/plain"
print(headers["accept"])
print(list(headers))
print(list(headers.lower_items()))
print(headers == {"ACCEPT": "text/plain"})
"""

LOOKUP_HARNESS = """from requests.structures import LookupDict

status = LookupDict("http-status")
status.ok = 200
print(repr(status))
print(status["ok"])
print(status.get("missing"))
print(hasattr(status, "ok"))
print(hasattr(status, "missing"))
"""


@dataclass(frozen=True)
class PythonPilotSpec:
    project: str
    unit_name: str
    source_path: Path
    test_source_path: Path
    test_target: str
    harness: str
    mutation: str
    mutate: Callable[[str, str], str]


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _class_node(source: str, name: str) -> ast.ClassDef:
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise ValueError(f"class {name!r} not found")


def _replace_class(module_source: str, variant_source: str, name: str) -> str:
    module_node = _class_node(module_source, name)
    variant_node = _class_node(variant_source, name)
    module_lines = module_source.splitlines(keepends=True)
    variant_lines = variant_source.splitlines(keepends=True)
    replacement = "".join(
        variant_lines[variant_node.lineno - 1 : variant_node.end_lineno]
    )
    if not replacement.endswith("\n"):
        replacement += "\n"
    return "".join(
        module_lines[: module_node.lineno - 1]
        + [replacement]
        + module_lines[module_node.end_lineno :]
    )


def _offset(source: str, line: int, column: int) -> int:
    lines = source.splitlines(keepends=True)
    return sum(len(item) for item in lines[: line - 1]) + column


def _inject_equality_bug(source: str, class_name: str) -> str:
    """Invert the class's dict(...) == dict(...) comparison."""
    class_node = _class_node(source, class_name)
    matches: list[ast.Compare] = []
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.Eq) or len(node.comparators) != 1:
            continue
        operands = (node.left, node.comparators[0])
        if all(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == "dict"
            for item in operands
        ):
            matches.append(node)
    if len(matches) != 1:
        raise ValueError(f"expected one dict equality, found {len(matches)}")
    comparison = matches[0]
    left_end = _offset(
        source, comparison.left.end_lineno, comparison.left.end_col_offset
    )
    right_start = _offset(
        source, comparison.comparators[0].lineno, comparison.comparators[0].col_offset
    )
    between = source[left_end:right_start]
    operator_at = between.find("==")
    if operator_at < 0:
        raise ValueError("equality token not found")
    start = left_end + operator_at
    return source[:start] + "!=" + source[start + 2 :]


def _inject_membership_bug(source: str, class_name: str) -> str:
    """Invert the class's `key in self.__dict__` membership test."""
    class_node = _class_node(source, class_name)
    matches: list[ast.Compare] = []
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.In) or len(node.comparators) != 1:
            continue
        right = node.comparators[0]
        if (
            isinstance(right, ast.Attribute)
            and right.attr == "__dict__"
            and isinstance(right.value, ast.Name)
            and right.value.id == "self"
        ):
            matches.append(node)
    if len(matches) != 1:
        raise ValueError(
            f"expected one self.__dict__ membership test, found {len(matches)}"
        )
    comparison = matches[0]
    left_end = _offset(
        source, comparison.left.end_lineno, comparison.left.end_col_offset
    )
    right_start = _offset(
        source, comparison.comparators[0].lineno, comparison.comparators[0].col_offset
    )
    between = source[left_end:right_start]
    operator_at = between.find("in")
    if operator_at < 0:
        raise ValueError("membership token not found")
    start = left_end + operator_at
    return source[:start] + "not in" + source[start + 2 :]


def _inject_version_length_bug(source: str, class_name: str) -> str:
    """Invert `len(parts) == 3` in the version-string parser."""
    class_node = _class_node(source, class_name)
    matches: list[ast.Compare] = []
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.Eq) or len(node.comparators) != 1:
            continue
        left = node.left
        right = node.comparators[0]
        if (
            isinstance(left, ast.Call)
            and isinstance(left.func, ast.Name)
            and left.func.id == "len"
            and isinstance(right, ast.Constant)
            and right.value == 3
        ):
            matches.append(node)
    if len(matches) != 1:
        raise ValueError(f"expected one version-length equality, found {len(matches)}")
    comparison = matches[0]
    left_end = _offset(
        source, comparison.left.end_lineno, comparison.left.end_col_offset
    )
    right_start = _offset(
        source, comparison.comparators[0].lineno, comparison.comparators[0].col_offset
    )
    between = source[left_end:right_start]
    operator_at = between.find("==")
    if operator_at < 0:
        raise ValueError("version-length equality token not found")
    start = left_end + operator_at
    return source[:start] + "!=" + source[start + 2 :]


def _single_line_change(original: str, changed: str) -> tuple[str, str]:
    original_lines = original.splitlines()
    changed_lines = changed.splitlines()
    removed = [line for line in original_lines if line not in changed_lines]
    added = [line for line in changed_lines if line not in original_lines]
    if len(removed) != 1 or len(added) != 1:
        raise ValueError("mutation must replace exactly one unique source line")
    return removed[0], added[0]


PILOT_SPECS = (
    PythonPilotSpec(
        project="requests",
        unit_name="CaseInsensitiveDict",
        source_path=Path("src/requests/structures.py"),
        test_source_path=Path("tests/test_structures.py"),
        test_target="tests/test_structures.py::TestCaseInsensitiveDict",
        harness=CASE_INSENSITIVE_HARNESS,
        mutation="invert_dict_equality",
        mutate=_inject_equality_bug,
    ),
    PythonPilotSpec(
        project="requests",
        unit_name="LookupDict",
        source_path=Path("src/requests/structures.py"),
        test_source_path=Path("tests/test_structures.py"),
        test_target="tests/test_structures.py::TestLookupDict",
        harness=LOOKUP_HARNESS,
        mutation="invert_attribute_membership",
        mutate=_inject_membership_bug,
    ),
    PythonPilotSpec(
        project="attrs",
        unit_name="VersionInfo",
        source_path=Path("src/attr/_version_info.py"),
        test_source_path=Path("tests/test_version_info.py"),
        test_target="tests/test_version_info.py",
        harness="""from attr import VersionInfo

version = VersionInfo._from_version_string("19.2.0")
print(version)
print(version.releaselevel)
print(version == (19, 2))
print(version < (20,))
print(version > (19, 1, 9))
""",
        mutation="invert_version_component_count",
        mutate=_inject_version_length_bug,
    ),
)


def _run(
    command: list[str], *, cwd: Path, python_path: Path
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(python_path)
    # Every execution needs a fresh bytecode cache. Several mutations preserve
    # file size and may be written within one timestamp tick, which can make a
    # subsequent interpreter accept stale pyc files as current.
    with tempfile.TemporaryDirectory(prefix="readability-pilot-pycache-") as cache:
        environment["PYTHONPYCACHEPREFIX"] = cache
        return subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
            check=False,
        )


def _write_jsonl(path: Path, records: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_python_pilot(workspace: Path, output: Path) -> dict[str, object]:
    """Build validated behavior and repair tasks for selected Python classes."""
    candidate_path = workspace / "data/experiments/behavior-prediction/candidates.jsonl"
    candidates = {
        str(row["unit_name"]): row
        for row in _jsonl(candidate_path)
        if row["language"] == "python"
    }

    behavior_tasks: list[dict[str, object]] = []
    repair_tasks: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="readability-python-pilot-") as directory:
        projects: dict[str, Path] = {}
        for spec in PILOT_SPECS:
            raw_project = workspace / "data/raw" / spec.project
            if spec.project not in projects:
                project_copy = Path(directory) / spec.project
                shutil.copytree(
                    raw_project,
                    project_copy,
                    ignore=shutil.ignore_patterns(
                        ".git", "__pycache__", ".pytest_cache"
                    ),
                )
                projects[spec.project] = project_copy
            project = projects[spec.project]
            candidate = candidates[spec.unit_name]
            original_module = (raw_project / spec.source_path).read_text(
                encoding="utf-8"
            )
            test_source = (raw_project / spec.test_source_path).read_text(
                encoding="utf-8"
            )
            target = project / spec.source_path
            unit_outputs: set[tuple[str, ...]] = set()
            for variant in candidate["variants"]:
                if (
                    variant["interference"] is not None
                    and not variant["changed_from_original"]
                ):
                    validation_rows.append(
                        {
                            "unit_name": spec.unit_name,
                            "variant_id": variant["variant_id"],
                            "interference": variant["interference"],
                            "changed_from_original": False,
                            "excluded_reason": "textually_identical_to_original",
                        }
                    )
                    continue
                variant_path = workspace / str(variant["local_path"])
                variant_source = variant_path.read_text(encoding="utf-8")
                restored = _replace_class(
                    original_module, variant_source, spec.unit_name
                )
                target.write_text(restored, encoding="utf-8")

                clean = _run(
                    [sys.executable, "-m", "pytest", "-q", spec.test_target],
                    cwd=project,
                    python_path=project / "src",
                )
                harness = _run(
                    [sys.executable, "-c", spec.harness],
                    cwd=project,
                    python_path=project / "src",
                )
                row: dict[str, object] = {
                    "unit_name": spec.unit_name,
                    "variant_id": variant["variant_id"],
                    "interference": variant["interference"],
                    "changed_from_original": variant["changed_from_original"],
                    "clean_tests_passed": clean.returncode == 0,
                    "clean_test_returncode": clean.returncode,
                    "behavior_executed": harness.returncode == 0,
                }
                if clean.returncode == 0 and harness.returncode == 0:
                    stdout_lines = harness.stdout.splitlines()
                    unit_outputs.add(tuple(stdout_lines))
                    behavior_tasks.append(
                        {
                            "task_id": f"behavior-{variant['variant_id']}",
                            "experiment": "behavior-prediction",
                            "language": "python",
                            "project": spec.project,
                            "base_sample_id": candidate["base_sample_id"],
                            "variant_id": variant["variant_id"],
                            "interference": variant["interference"],
                            "unit_name": spec.unit_name,
                            "source_path": spec.source_path.as_posix(),
                            "expected": {"stdout_lines": stdout_lines},
                            "prompt": behavior_prediction_prompt(
                                language="Python",
                                source_path=spec.source_path.as_posix(),
                                source_code=variant_source,
                                harness_code=spec.harness,
                            ),
                        }
                    )
                    row["stdout_lines"] = stdout_lines

                    try:
                        buggy_variant = spec.mutate(variant_source, spec.unit_name)
                        repaired_line, buggy_line = _single_line_change(
                            variant_source, buggy_variant
                        )
                        buggy_module = _replace_class(
                            original_module, buggy_variant, spec.unit_name
                        )
                        target.write_text(buggy_module, encoding="utf-8")
                        mutant = _run(
                            [sys.executable, "-m", "pytest", "-q", spec.test_target],
                            cwd=project,
                            python_path=project / "src",
                        )
                        row["mutant_killed"] = mutant.returncode != 0
                        row["mutant_test_returncode"] = mutant.returncode
                        if mutant.returncode != 0:
                            repair_tasks.append(
                                {
                                    "task_id": f"repair-{variant['variant_id']}",
                                    "experiment": "test-guided-repair",
                                    "language": "python",
                                    "project": spec.project,
                                    "base_sample_id": candidate["base_sample_id"],
                                    "variant_id": variant["variant_id"],
                                    "interference": variant["interference"],
                                    "unit_name": spec.unit_name,
                                    "source_path": spec.source_path.as_posix(),
                                    "mutation": spec.mutation,
                                    "expected": {
                                        "removed_line": buggy_line,
                                        "added_line": repaired_line,
                                    },
                                    "prompt": test_guided_repair_prompt(
                                        language="Python",
                                        source_path=spec.source_path.as_posix(),
                                        buggy_source=buggy_variant,
                                        test_source=test_source,
                                        test_command=f"python -m pytest -q {spec.test_target}",
                                        failure_output=mutant.stdout[-6000:],
                                    ),
                                }
                            )
                    except ValueError as error:
                        row["mutant_killed"] = False
                        row["mutation_error"] = str(error)
                validation_rows.append(row)
            if len(unit_outputs) != 1:
                raise RuntimeError(f"{spec.unit_name} variants do not share one oracle")

    combined = behavior_tasks + repair_tasks
    output.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output / "behavior-tasks.jsonl", behavior_tasks)
    _write_jsonl(output / "repair-tasks.jsonl", repair_tasks)
    _write_jsonl(output / "tasks.jsonl", combined)
    _write_jsonl(output / "validation.jsonl", validation_rows)
    report = {
        "schema_version": 1,
        "status": "executable_pilot",
        "projects": sorted({spec.project for spec in PILOT_SPECS}),
        "unit_names": [spec.unit_name for spec in PILOT_SPECS],
        "base_classes": len(PILOT_SPECS),
        "variants_considered": sum(
            len(candidates[spec.unit_name]["variants"]) for spec in PILOT_SPECS
        ),
        "behavior_tasks": len(behavior_tasks),
        "repair_tasks": len(repair_tasks),
        "tasks": len(combined),
        "equal_behavior_oracle": True,
        "source_dataset_modified": False,
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
