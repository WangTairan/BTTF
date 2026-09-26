"""Build model-facing tasks from natively validated repository holes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from readability_experiments.common.paths import default_workspace

from .builder import HOLE, _read_jsonl, _write_jsonl
from .catalog import REPOSITORIES
from .discovery import verify_manifest
from .prompts import span_completion_prompt

EXPECTED_KIND = "repository_span_completion_validation"
SPAN_KEYS = {"method_body": "method_span", "statement": "statement_span"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _replace_span(source: str, span: dict[str, Any], replacement: str) -> str:
    encoded = source.encode("utf-8")
    start = int(span["start_byte"])
    end = int(span["end_byte"])
    return (encoded[:start] + replacement.encode("utf-8") + encoded[end:]).decode(
        "utf-8"
    )


def build_tasks(
    *,
    workspace: Path,
    targets_path: Path,
    holes_path: Path,
    output: Path,
    language: str,
    granularities: tuple[str, ...],
    limit_targets: int | None,
    shortest_first: bool,
) -> dict[str, Any]:
    verification = verify_manifest(workspace, targets_path)
    holes = {
        (str(row["target_id"]), str(row["granularity"]))
        for row in _read_jsonl(holes_path)
        if row.get("status") == "usable" and row.get("test_sensitive") is True
    }
    rows = [
        row
        for row in _read_jsonl(targets_path)
        if str(row["language"]) == language
    ]
    if shortest_first:
        rows.sort(
            key=lambda row: (
                int(row["method_span"]["byte_count"]),
                str(row["target_id"]),
            )
        )
    if limit_targets is not None:
        rows = rows[:limit_targets]

    specs = {spec.repository_id: spec for spec in REPOSITORIES}
    tasks: list[dict[str, Any]] = []
    for row in rows:
        repository_id = str(row["repository_id"])
        repository = (
            workspace / "data/raw/completion_pilot" / specs[repository_id].directory
        )
        source = (repository / str(row["source_path"])).read_text(encoding="utf-8")
        if _sha256(source) != row["source_sha256"]:
            raise ValueError(f"source hash mismatch for {row['target_id']}")
        for granularity in granularities:
            key = (str(row["target_id"]), granularity)
            if key not in holes:
                continue
            span = dict(row[SPAN_KEYS[granularity]])
            source_with_hole = _replace_span(source, span, HOLE)
            if _sha256(source_with_hole) != span["hole_context_sha256"]:
                raise ValueError(
                    f"hole hash mismatch for {row['target_id']}:{granularity}"
                )
            tasks.append(
                {
                    "schema_version": 1,
                    "task_id": (
                        f"recent-completion--{repository_id}--{row['target_id']}--"
                        f"{granularity.replace('_', '-')}"
                    ),
                    "experiment": "recent-repository-span-completion",
                    "condition": "original",
                    "expected_kind": EXPECTED_KIND,
                    "dynamic_prevalidated": True,
                    "repository_id": repository_id,
                    "repository_url": row["repository_url"],
                    "license_spdx": row["license_spdx"],
                    "language": language,
                    "pinned_commit": row["pinned_commit"],
                    "target_origin_commit": row["method_origin_commit"],
                    "target_origin_date": row["method_origin_date"],
                    "target_id": row["target_id"],
                    "qualified_name": row["qualified_name"],
                    "source_path": row["source_path"],
                    "source_sha256": row["source_sha256"],
                    "granularity": granularity,
                    "span": span,
                    "completion_sha256": span["completion_sha256"],
                    "source_with_hole": source_with_hole,
                    "prompt_source_sha256": _sha256(source_with_hole),
                    "gold_source_sha256": row["source_sha256"],
                    "test_command": row["test_command"],
                    "test_paths": row["test_paths"],
                    "prompt_template": "repository-span-completion-v1",
                    "prompt": span_completion_prompt(
                        language=language,
                        repository=repository_id,
                        source_path=str(row["source_path"]),
                        source_with_hole=source_with_hole,
                    ),
                }
            )

    if not tasks:
        raise ValueError("no natively validated holes matched the requested filters")
    _write_jsonl(output, tasks)
    report = {
        "schema_version": 1,
        "experiment": "recent-repository-span-completion",
        "language": language,
        "target_count": len({str(task["target_id"]) for task in tasks}),
        "task_count": len(tasks),
        "by_granularity": {
            granularity: sum(task["granularity"] == granularity for task in tasks)
            for granularity in granularities
        },
        "model_input_contains_tests": False,
        "model_input_contains_gold_completion": False,
        "source_manifest_verification": verification,
        "task_manifest_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    output.with_suffix(".report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build model-facing tasks from validated repository holes."
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--holes", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--language", choices=("java", "python"), default="python")
    parser.add_argument(
        "--granularity",
        action="append",
        choices=tuple(SPAN_KEYS),
        dest="granularities",
    )
    parser.add_argument("--limit-targets", type=int)
    parser.add_argument(
        "--shortest-first",
        action="store_true",
        help="use the smallest method bodies first for a cheap solvability pilot",
    )
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    validation = (
        workspace / "data/experiments/recent-repository-completion/native-validation"
    )
    targets = (args.targets or validation / "balanced_targets.jsonl").resolve()
    holes = (args.holes or validation / "balanced_holes.jsonl").resolve()
    output = (
        args.output
        or workspace
        / "data/experiments/recent-repository-completion/model-tasks"
        / f"{args.language}.jsonl"
    ).resolve()
    report = build_tasks(
        workspace=workspace,
        targets_path=targets,
        holes_path=holes,
        output=output,
        language=args.language,
        granularities=tuple(args.granularities or SPAN_KEYS),
        limit_targets=args.limit_targets,
        shortest_first=args.shortest_first,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
