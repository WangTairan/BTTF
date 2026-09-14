"""Build complete, lightweight catalogs for external repair benchmarks.

The catalogs contain every benchmark instance and all locally available metadata.
Project repositories are deliberately checked out on demand by the validation layer;
duplicating a repository for every bug would be both wasteful and harder to audit.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_ASSIGNMENT = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"(.*)"\s*$')
_DIFF_PATH = re.compile(r"^diff --git a/(.+) b/(.+)$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _read_assignments(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig", errors="strict").splitlines():
        match = _ASSIGNMENT.match(line.rstrip("\r"))
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _patch_paths(path: Path) -> list[str]:
    paths: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _DIFF_PATH.match(line)
        if match and match.group(2) not in paths:
            paths.append(match.group(2))
    return paths


def _is_test_path(path: str) -> bool:
    parts = {part.lower() for part in Path(path).parts}
    name = Path(path).name.lower()
    return (
        bool(parts & {"test", "tests", "testing"})
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def bugsinpy_records(root: Path, workspace: Path) -> list[dict[str, object]]:
    projects = root / "projects"
    if not projects.is_dir():
        raise ValueError(f"BugsInPy projects directory not found: {projects}")
    records: list[dict[str, object]] = []
    for bug_info in sorted(
        projects.glob("*/bugs/*/bug.info"),
        key=lambda p: (p.parents[2].name, int(p.parent.name)),
    ):
        bug_dir = bug_info.parent
        project_dir = bug_dir.parents[1]
        project = project_dir.name
        bug_id = bug_dir.name
        metadata = _read_assignments(bug_info)
        project_metadata = _read_assignments(project_dir / "project.info")
        patch = bug_dir / "bug_patch.txt"
        test_script = bug_dir / "run_test.sh"
        paths = _patch_paths(patch)
        source_paths = [
            path for path in paths if path.endswith(".py") and not _is_test_path(path)
        ]
        test_files = [item for item in metadata.get("test_file", "").split(";") if item]
        test_commands = [
            line.rstrip("\r")
            for line in test_script.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        records.append(
            {
                "schema_version": 1,
                "benchmark": "bugsinpy",
                "instance_id": f"bugsinpy__{project}__{bug_id}",
                "language": "python",
                "project": project,
                "bug_id": bug_id,
                "buggy_revision": metadata.get("buggy_commit_id"),
                "fixed_revision": metadata.get("fixed_commit_id"),
                "runtime_version": metadata.get("python_version"),
                "repository_url": project_metadata.get("github_url"),
                "test_files": test_files,
                "test_commands": test_commands,
                "patch_paths": paths,
                "production_source_paths": source_paths,
                "production_source_file_count": len(source_paths),
                "single_production_source_file": len(source_paths) == 1,
                "patch_sha256": _sha256(patch),
                "metadata_path": _relative(bug_dir, workspace),
            }
        )
    return records


def _active_bug_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    if not rows:
        return []
    header = [cell.strip() for cell in rows[0]]
    if "bug.id" in header:
        return [
            dict(zip(header, (cell.strip() for cell in row))) for row in rows[1:] if row
        ]
    return [{"bug.id": row[0].strip()} for row in rows if row and row[0].strip()]


def _first_existing(*paths: Path) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def _lines(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    ]


def _defects4j_trigger_tests(path: Path | None) -> list[str]:
    """Extract test identifiers while discarding the recorded stack traces."""
    return [line[4:].strip() for line in _lines(path) if line.startswith("--- ")]


def defects4j_records(root: Path, workspace: Path) -> list[dict[str, object]]:
    projects = root / "framework" / "projects"
    if not projects.is_dir():
        raise ValueError(f"Defects4J projects directory not found: {projects}")
    records: list[dict[str, object]] = []
    for active in sorted(projects.glob("*/active-bugs.csv")):
        project_dir = active.parent
        project = project_dir.name
        for row in _active_bug_rows(active):
            bug_id = row["bug.id"]
            patch = _first_existing(
                project_dir / "patches" / f"{bug_id}.src.patch",
                project_dir / "patches" / f"{bug_id}.patch",
            )
            modified = _first_existing(
                project_dir / "modified_classes" / f"{bug_id}.src",
                project_dir / "modified_classes" / bug_id,
            )
            triggering = _first_existing(
                project_dir / "trigger_tests" / bug_id,
                project_dir / "trigger_tests" / f"{bug_id}.tests",
                project_dir / "triggering_tests" / bug_id,
            )
            paths = _patch_paths(patch) if patch else []
            source_paths = [
                path
                for path in paths
                if path.endswith(".java") and not _is_test_path(path)
            ]
            modified_classes = _lines(modified)
            records.append(
                {
                    "schema_version": 1,
                    "benchmark": "defects4j",
                    "instance_id": f"defects4j__{project}__{bug_id}",
                    "language": "java",
                    "project": project,
                    "bug_id": bug_id,
                    "buggy_revision": f"{bug_id}b",
                    "fixed_revision": f"{bug_id}f",
                    "buggy_commit": row.get("revision.id.buggy") or None,
                    "fixed_commit": row.get("revision.id.fixed") or None,
                    "issue_id": row.get("report.id") or None,
                    "issue_url": row.get("report.url") or None,
                    "runtime_version": "11",
                    "repository_url": row.get("project.repository") or None,
                    "trigger_tests": _defects4j_trigger_tests(triggering),
                    "modified_classes": modified_classes,
                    "patch_paths": paths,
                    "production_source_paths": source_paths,
                    "production_source_file_count": len(source_paths)
                    or len(modified_classes),
                    "single_production_source_file": (
                        len(source_paths) == 1 if paths else len(modified_classes) == 1
                    ),
                    "patch_sha256": _sha256(patch) if patch else None,
                    "metadata_path": _relative(project_dir, workspace),
                }
            )
    return records


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_benchmark_catalogs(
    defects4j_root: Path,
    bugsinpy_root: Path,
    output: Path,
    workspace: Path,
) -> dict[str, object]:
    """Write complete catalogs without checking out per-instance repositories."""
    catalogs = {
        "defects4j": defects4j_records(defects4j_root.resolve(), workspace),
        "bugsinpy": bugsinpy_records(bugsinpy_root.resolve(), workspace),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        reports: dict[str, object] = {}
        for benchmark, records in catalogs.items():
            _write_jsonl(staging / f"{benchmark}.jsonl", records)
            reports[benchmark] = {
                "instance_count": len(records),
                "counts_by_project": dict(
                    sorted(Counter(str(row["project"]) for row in records).items())
                ),
                "single_production_source_file_count": sum(
                    bool(row["single_production_source_file"]) for row in records
                ),
            }
        report = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "storage_policy": "complete metadata catalog; source repositories checked out on demand",
            "benchmarks": reports,
        }
        (staging / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
        return report
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
