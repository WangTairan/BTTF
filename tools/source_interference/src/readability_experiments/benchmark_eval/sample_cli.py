"""Create fixed, stratified task manifests from static benchmark validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext
from readability_experiments.prompts import benchmark_repair_prompt

from ..common.paths import default_workspace
from .diagnostics import RepairEvidence, fetch_bugsinpy_test_sources, repair_evidence
from .static_validation import _apply, _read_jsonl, load_source_pair

DEFAULT_SEED = 20260823


def _rank(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def _allocate(groups: dict[str, list[dict[str, object]]], total: int) -> dict[str, int]:
    if total > sum(map(len, groups.values())):
        raise ValueError("requested sample is larger than the eligible population")
    projects = sorted(groups)
    quotas = {project: 0 for project in projects}
    remaining = total
    if total < len(projects):
        # A small pilot should cover projects rather than spending nearly all
        # slots on the largest repository.
        for project in sorted(projects, key=lambda item: (-len(groups[item]), item))[
            :total
        ]:
            quotas[project] = 1
        return quotas
    if total >= len(projects):
        for project in projects:
            quotas[project] = 1
        remaining -= len(projects)
    capacity = {project: len(groups[project]) - quotas[project] for project in projects}
    while remaining:
        available = {project: count for project, count in capacity.items() if count > 0}
        denominator = sum(available.values())
        shares = {
            project: remaining * count / denominator
            for project, count in available.items()
        }
        additions = {
            project: min(capacity[project], math.floor(share))
            for project, share in shares.items()
        }
        assigned = sum(additions.values())
        if assigned == 0:
            project = max(
                available, key=lambda item: (shares[item] % 1, available[item], item)
            )
            additions[project] = 1
            assigned = 1
        for project, count in additions.items():
            quotas[project] += count
            capacity[project] -= count
        remaining -= assigned
    return quotas


def _select_language(
    rows: list[dict[str, object]], count: int, seed: int
) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row["project"])].append(row)
    quotas = _allocate(groups, count)
    selected = []
    for project in sorted(groups):
        ordered = sorted(
            groups[project],
            key=lambda row: (int(row["source_bytes"]), str(row["instance_id"])),
        )
        quota = quotas[project]
        for index in range(quota):
            start = index * len(ordered) // quota
            stop = (index + 1) * len(ordered) // quota
            bucket = ordered[start:stop]
            selected.append(
                min(bucket, key=lambda row: _rank(seed, str(row["instance_id"])))
            )
    return sorted(
        selected,
        key=lambda row: (
            str(row["language"]),
            str(row["project"]),
            str(row["instance_id"]),
        ),
    )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _build_tasks(
    selected: list[dict[str, object]],
    catalogs: dict[str, dict[str, object]],
    defects4j_repos: Path,
    bugsinpy_repos: Path,
    source_cache: Path,
    seed: int,
    workspace: Path,
    evidence_cache: dict[str, RepairEvidence],
) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for selection in selected:
        record = catalogs[str(selection["instance_id"])]
        pair = load_source_pair(record, defects4j_repos, bugsinpy_repos, source_cache)
        instance_id = str(record["instance_id"])
        if instance_id not in evidence_cache:
            evidence_cache[instance_id] = repair_evidence(
                record, workspace, defects4j_repos, bugsinpy_repos
            )
        evidence = evidence_cache[instance_id]
        if not evidence.test_code:
            raise ValueError(f"no relevant test code found for {record['instance_id']}")
        plugins = (
            JAVA_INTERFERENCES if record["language"] == "java" else PYTHON_INTERFERENCES
        )
        variants: list[tuple[str, bytes]] = [("original", pair.buggy)]
        identity = f"{record['instance_id']}:{pair.path}:{pair.class_name}"
        for plugin in plugins:
            variants.append(
                (
                    str(plugin.slug),
                    _apply(
                        str(record["language"]),
                        pair.buggy,
                        pair.class_name,
                        plugin,
                        InterferenceContext(seed, identity),
                    ),
                )
            )
        for condition, source in variants:
            task_id = f"repair--{record['instance_id']}--{condition}"
            tasks.append(
                {
                    "task_id": task_id,
                    "experiment": "test-guided-repair",
                    "expected_kind": "external_patch_validation",
                    "prompt_template": "single-message-repair-v2",
                    "language": record["language"],
                    "benchmark": record["benchmark"],
                    "project": record["project"],
                    "bug_id": record["bug_id"],
                    "base_task_id": record["instance_id"],
                    "condition": condition,
                    "interference_seed": seed,
                    "source_path": pair.path,
                    "class_name": pair.class_name,
                    "developer_patch_sha256": record.get("patch_sha256"),
                    "prompt": benchmark_repair_prompt(
                        language="Java" if record["language"] == "java" else "Python",
                        source_path=pair.path,
                        buggy_source=source.decode("utf-8"),
                        test_code=evidence.test_code,
                        failure_output=evidence.failure_output,
                    ),
                }
            )
    return tasks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-sample-repair-tasks",
        description="Fix formal and pilot complete-case samples and build prompt-bearing task JSONL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--formal-per-language", type=int, default=100)
    parser.add_argument("--pilot-per-language", type=int, default=10)
    parser.add_argument(
        "--fetch-missing-test-sources",
        action="store_true",
        help="download selected BugsInPy test blobs into the local benchmark cache",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/experiments/agent-readability/fixed-samples"),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()
    output = args.output if args.output.is_absolute() else workspace / args.output
    validation_root = workspace / "data/experiments/agent-readability"
    validation = [
        row
        for language in ("java", "python")
        for row in _read_jsonl(
            validation_root / f"static-validation-{language}/validation.jsonl"
        )
        if row["status"] == "usable"
        and len(row.get("conditions", [])) == 13
        and all(condition["status"] == "usable" for condition in row["conditions"])
    ]
    by_language = {
        language: [row for row in validation if row["language"] == language]
        for language in ("java", "python")
    }
    catalog_root = workspace / "data/benchmarks/catalogs/repair-benchmarks"
    catalogs = {
        str(row["instance_id"]): row
        for name in ("defects4j", "bugsinpy")
        for row in _read_jsonl(catalog_root / f"{name}.jsonl")
    }
    d4j = workspace / "data/benchmarks/frameworks/defects4j/project_repos"
    bip = workspace / "data/benchmarks/repositories/bugsinpy"
    cache = workspace / "data/benchmarks/cache/static-sources"
    for row in validation:
        pair = load_source_pair(catalogs[str(row["instance_id"])], d4j, bip, cache)
        row["source_bytes"] = len(pair.buggy)
    formal = [
        row
        for language in ("java", "python")
        for row in _select_language(
            by_language[language], args.formal_per_language, args.seed
        )
    ]
    formal_ids = {str(row["instance_id"]) for row in formal}
    pilot = [
        row
        for language in ("java", "python")
        for row in _select_language(
            [
                item
                for item in by_language[language]
                if str(item["instance_id"]) in formal_ids
            ],
            args.pilot_per_language,
            args.seed + 1,
        )
    ]
    if args.fetch_missing_test_sources:
        fetch_bugsinpy_test_sources(
            [catalogs[str(row["instance_id"])] for row in formal], workspace
        )
    artifacts: dict[str, dict[str, object]] = {}
    evidence_cache: dict[str, RepairEvidence] = {}
    for name, selected in (("formal", formal), ("pilot", pilot)):
        manifest = [
            {
                "instance_id": row["instance_id"],
                "language": row["language"],
                "project": row["project"],
                "class_name": row["class_name"],
                "source_path": row["source_path"],
                "source_bytes": row["source_bytes"],
            }
            for row in selected
        ]
        tasks = _build_tasks(
            selected, catalogs, d4j, bip, cache, args.seed, workspace, evidence_cache
        )
        base_path = output / name / "base-tasks.jsonl"
        tasks_path = output / name / "tasks.jsonl"
        _write_jsonl(base_path, manifest)
        _write_jsonl(tasks_path, tasks)
        artifacts[name] = {
            "base_manifest_sha256": hashlib.sha256(base_path.read_bytes()).hexdigest(),
            "task_manifest_sha256": hashlib.sha256(tasks_path.read_bytes()).hexdigest(),
        }
    report = {
        "schema_version": 1,
        "seed": args.seed,
        "prompt_template": "single-message-repair-v2",
        "prompt_evidence": {
            "base_tasks_with_test_code": sum(
                bool(item.test_code) for item in evidence_cache.values()
            ),
            "base_tasks_with_failure_output": sum(
                bool(item.failure_output) for item in evidence_cache.values()
            ),
            "policy": "one shared evidence bundle per base task; only source code changes across conditions",
        },
        "sampling": "project- and source-size-stratified complete cases; pilot is a fixed subset of formal",
        "formal": {
            "base_tasks": len(formal),
            "llm_tasks": len(formal) * 14,
            **artifacts["formal"],
        },
        "pilot": {
            "base_tasks": len(pilot),
            "llm_tasks": len(pilot) * 14,
            **artifacts["pilot"],
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
