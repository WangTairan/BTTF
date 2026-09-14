"""Batch entry point for static interference validation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..common.paths import default_workspace
from .static_validation import _read_jsonl, summarize, validate_record_static

DEFAULT_SEED = 20260823


def _raw_github_url(repository_url: str, revision: str, path: str) -> str:
    marker = "github.com/"
    if marker not in repository_url:
        raise ValueError(f"unsupported repository URL: {repository_url}")
    repository = repository_url.split(marker, 1)[1].rstrip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]
    quoted_path = "/".join(
        urllib.parse.quote(part, safe="") for part in path.split("/")
    )
    return f"https://raw.githubusercontent.com/{repository}/{revision}/{quoted_path}"


def _download(url: str, destination: Path, timeout: int) -> None:
    if destination.is_file():
        return
    request = urllib.request.Request(
        url, headers={"User-Agent": "readability-static-validation/1"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".download-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        Path(temporary).replace(destination)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _reconstruct_buggy(fixed: Path, buggy: Path, source_path: str, patch: Path) -> None:
    """Recover an old blob by applying the released developer patch in reverse."""
    with tempfile.TemporaryDirectory(prefix="readability-reverse-patch-") as directory:
        root = Path(directory)
        target = root / source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fixed.read_bytes())
        completed = subprocess.run(
            (
                "git",
                "apply",
                "--reverse",
                f"--include={source_path}",
                str(patch.resolve()),
            ),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip())
        buggy.parent.mkdir(parents=True, exist_ok=True)
        target.replace(buggy)


def cache_bugsinpy_sources(
    records: list[dict[str, object]],
    cache: Path,
    workspace: Path,
    workers: int,
    timeout: int,
) -> dict[str, str]:
    jobs: list[tuple[str, Path, str]] = []
    for record in records:
        if record["benchmark"] != "bugsinpy" or not record.get(
            "single_production_source_file"
        ):
            continue
        path = str(record["production_source_paths"][0])
        for side in ("buggy", "fixed"):
            revision = str(record[f"{side}_revision"])
            url = _raw_github_url(str(record["repository_url"]), revision, path)
            jobs.append(
                (
                    url,
                    cache / str(record["instance_id"]) / side,
                    str(record["instance_id"]),
                )
            )
    failures: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_download, url, destination, timeout): (instance_id, side)
            for url, destination, instance_id in jobs
            for side in (destination.name,)
        }
        for future in as_completed(futures):
            instance_id, side = futures[future]
            try:
                future.result()
            except Exception as error:
                failures[f"{instance_id}:{side}"] = f"{type(error).__name__}: {error}"
    for record in records:
        if record["benchmark"] != "bugsinpy" or not record.get(
            "single_production_source_file"
        ):
            continue
        instance_id = str(record["instance_id"])
        buggy = cache / instance_id / "buggy"
        fixed = cache / instance_id / "fixed"
        key = f"{instance_id}:buggy"
        if not buggy.is_file() and fixed.is_file():
            try:
                _reconstruct_buggy(
                    fixed,
                    buggy,
                    str(record["production_source_paths"][0]),
                    workspace / str(record["metadata_path"]) / "bug_patch.txt",
                )
                failures.pop(key, None)
            except Exception as error:
                failures[key] = f"reverse patch failed: {type(error).__name__}: {error}"
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-static-validation",
        description="Apply every interference to all repair-benchmark source pairs without executing projects.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--download-timeout", type=int, default=60)
    parser.add_argument(
        "--benchmark", choices=("all", "defects4j", "bugsinpy"), default="all"
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--catalog-root",
        type=Path,
        default=Path("data/benchmarks/catalogs/repair-benchmarks"),
    )
    parser.add_argument(
        "--defects4j-repos",
        type=Path,
        default=Path("data/benchmarks/frameworks/defects4j/project_repos"),
    )
    parser.add_argument(
        "--bugsinpy-repos",
        type=Path,
        default=Path("data/benchmarks/repositories/bugsinpy"),
    )
    parser.add_argument(
        "--source-cache",
        type=Path,
        default=Path("data/benchmarks/cache/static-sources"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/experiments/agent-readability/static-validation"),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else workspace / path

    catalog_root = resolve(args.catalog_root)
    names = ("defects4j", "bugsinpy") if args.benchmark == "all" else (args.benchmark,)
    records = [
        record
        for name in names
        for record in _read_jsonl(catalog_root / f"{name}.jsonl")
    ]
    if args.limit is not None:
        records = records[: args.limit]
    source_cache = resolve(args.source_cache)
    download_failures = cache_bugsinpy_sources(
        records, source_cache, workspace, args.workers, args.download_timeout
    )
    validated = [
        validate_record_static(
            record,
            resolve(args.defects4j_repos),
            resolve(args.bugsinpy_repos),
            args.seed,
            source_cache,
        )
        for record in records
    ]
    output = resolve(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "validation.jsonl").open("w", encoding="utf-8") as stream:
        for record in validated:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    report = summarize(validated, args.seed)
    report["download_failure_count"] = len(download_failures)
    report["download_failures"] = download_failures
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
