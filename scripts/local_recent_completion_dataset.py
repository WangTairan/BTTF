"""Archive or restore the pinned, offline Python completion benchmark."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets/recent_repository_completion/pytest_python"
WORKSPACE = ROOT / "artifacts/source_interference"
COMMIT = "53bc06b9933eb50b40cd904aa50bcd1b6cf2a49c"
SOURCE_ARCHIVE = "pytest-source.tar.gz"
TASK_ARCHIVE = "tasks.jsonl.gz"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def source_path(workspace: Path) -> Path:
    return workspace / "data/raw/completion_pilot/pytest"


def task_path(workspace: Path) -> Path:
    return workspace / "data/experiments/recent-repository-completion/python-interference/tasks.jsonl"


def report_path(workspace: Path) -> Path:
    return task_path(workspace).with_name("report.json")


def pack(workspace: Path) -> None:
    repository = source_path(workspace)
    tasks = task_path(workspace)
    report = report_path(workspace)
    for path in (repository, tasks, report):
        if not path.exists():
            raise FileNotFoundError(path)
    actual_commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit != COMMIT:
        raise ValueError(f"pytest checkout is {actual_commit}, expected {COMMIT}")
    commit_date = subprocess.check_output(
        ["git", "-C", str(repository), "show", "-s", "--format=%cI", COMMIT],
        text=True,
    ).strip()
    DATASET.mkdir(parents=True, exist_ok=True)
    archive = subprocess.check_output(["git", "-C", str(repository), "archive", COMMIT])
    with (DATASET / SOURCE_ARCHIVE).open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0, compresslevel=9) as zipped:
            zipped.write(archive)
    with (DATASET / TASK_ARCHIVE).open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0, compresslevel=9) as zipped:
            with tasks.open("rb") as original:
                shutil.copyfileobj(original, zipped)
    shutil.copyfile(report, DATASET / "report.json")
    summary = json.loads(report.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 1,
        "repository": "pytest-dev/pytest",
        "repository_url": "https://github.com/pytest-dev/pytest",
        "license_spdx": "MIT",
        "pinned_commit": COMMIT,
        "pinned_commit_date_utc": commit_date,
        "source_archive": SOURCE_ARCHIVE,
        "source_archive_sha256": digest(DATASET / SOURCE_ARCHIVE),
        "task_archive": TASK_ARCHIVE,
        "task_archive_sha256": digest(DATASET / TASK_ARCHIVE),
        "task_jsonl_sha256": digest(tasks),
        "report_sha256": digest(DATASET / "report.json"),
        "task_count": summary["usable_task_count"],
        "target_count": summary["target_count"],
        "original_task_count": summary["original_task_count"],
        "perturbed_task_count": summary["perturbed_task_count"],
        "seed": summary["seed"],
        "source_roots": ["src/_pytest"],
        "test_roots": ["testing"],
        "validation": "Each task contains its focused native pytest test_command and source hashes.",
    }
    (DATASET / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Archived {manifest['task_count']} tasks and pytest {COMMIT} in {DATASET}")


def verify_archives() -> dict:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    for filename, key in (
        (SOURCE_ARCHIVE, "source_archive_sha256"),
        (TASK_ARCHIVE, "task_archive_sha256"),
        ("report.json", "report_sha256"),
    ):
        if digest(DATASET / filename) != manifest[key]:
            raise ValueError(f"dataset checksum mismatch: {filename}")
    if manifest["pinned_commit"] != COMMIT:
        raise ValueError("dataset commit does not match the pinned runner commit")
    with gzip.open(DATASET / TASK_ARCHIVE, "rt", encoding="utf-8") as stream:
        tasks = [json.loads(line) for line in stream if line.strip()]
    if len(tasks) != manifest["task_count"]:
        raise ValueError("task count does not match the dataset manifest")
    source_hashes = {
        task["source_path"]: task["source_sha256"] for task in tasks
    }
    with tarfile.open(DATASET / SOURCE_ARCHIVE, "r:gz") as archive:
        for name, expected in source_hashes.items():
            member = archive.extractfile(name)
            if member is None or hashlib.sha256(member.read()).hexdigest() != expected:
                raise ValueError(f"source hash does not match task snapshot: {name}")
    return manifest


def restore(workspace: Path) -> None:
    manifest = verify_archives()
    repository = source_path(workspace)
    tasks = task_path(workspace)
    if repository.exists():
        print(f"Preserving existing checkout: {repository}")
    else:
        repository.mkdir(parents=True)
        with tarfile.open(DATASET / SOURCE_ARCHIVE, "r:gz") as archive:
            for member in archive:
                path = Path(member.name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError(f"unsafe archive member: {member.name}")
                destination = repository / path
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as src, destination.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                else:
                    raise ValueError(f"unsupported archive member: {member.name}")
    if tasks.exists():
        if digest(tasks) != manifest["task_jsonl_sha256"]:
            raise ValueError(f"existing task manifest differs from local dataset: {tasks}")
        print(f"Preserving matching task manifest: {tasks}")
    else:
        tasks.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(DATASET / TASK_ARCHIVE, "rb") as src, tasks.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if digest(tasks) != manifest["task_jsonl_sha256"]:
            raise ValueError("restored task manifest checksum mismatch")
    if not report_path(workspace).exists():
        shutil.copyfile(DATASET / "report.json", report_path(workspace))
    print("Local completion dataset ready; no network access used.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("pack", "verify", "restore"))
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    args = parser.parse_args()
    if args.action == "pack":
        pack(args.workspace)
    elif args.action == "verify":
        manifest = verify_archives()
        print(f"Verified {manifest['task_count']} local tasks and source archive.")
    else:
        restore(args.workspace)


if __name__ == "__main__":
    main()
