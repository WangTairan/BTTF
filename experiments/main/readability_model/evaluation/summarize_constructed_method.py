"""Summarize paired constructed variants from a shared method result file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS, method_output_key
from src.experiments.paths import safe_path_part

from .evaluate_constructed_variants import summarize_paired_variants


SUPPORTED_DATASETS = (
    "java_comparative_obfuscation",
    "python_comparative_degradation",
)
METHOD_RESULT_KEYS = {
    "posnett": method_output_key("posnett"),
    "scalabrino": method_output_key("scalabrino"),
    "dorn": method_output_key("dorn"),
    "mi_convnet_cr": method_output_key("mi_convnet_cr"),
    "llm": method_output_key("llm"),
    "lloc": "lloc_baseline",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute matched-original response rates for one completed method run."
    )
    parser.add_argument("--dataset", choices=SUPPORTED_DATASETS, required=True)
    parser.add_argument("--method", choices=tuple(METHOD_RESULT_KEYS), required=True)
    parser.add_argument(
        "--model",
        help="Configured model key for methods stored in model-specific result directories.",
    )
    parser.add_argument("--results-root", type=Path, default=Path("results/methods"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    method_key = METHOD_RESULT_KEYS[args.method]
    result_dir = args.results_root / method_key / args.dataset
    if args.method == "llm":
        if not args.model:
            raise SystemExit("--model is required when --method llm")
        result_dir /= safe_path_part(args.model)
    elif args.model:
        raise SystemExit("--model is only valid when --method llm")
    summary_path = result_dir / "summary.json"
    if not summary_path.is_file():
        raise SystemExit(f"Missing method result summary: {summary_path}")

    method_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    result_rows = method_summary.get("results")
    if not isinstance(result_rows, list):
        raise ValueError(f"Method summary has no result rows: {summary_path}")

    items = load_code_dataset(DATASETS[args.dataset].path)
    item_by_id = {item.task_id: item for item in items}
    result_by_id = {str(row["task_id"]): row for row in result_rows}
    if set(result_by_id) != set(item_by_id):
        raise ValueError(
            "Dataset/method identity mismatch: "
            f"missing_results={len(set(item_by_id) - set(result_by_id))}, "
            f"unknown_results={len(set(result_by_id) - set(item_by_id))}"
        )

    excluded_groups = failed_groups(items, result_by_id)
    rows = [
        paired_row(result_by_id[item.task_id], item.metadata, method=args.method)
        for item in items
        if str(item.metadata["group_id"]) not in excluded_groups
    ]
    if not rows:
        raise ValueError(f"{args.method} produced no complete groups for {args.dataset}")
    paired_summary = {
        **summarize_paired_variants(rows),
        "dataset": args.dataset,
        "method": args.method,
        "method_result": str(summary_path),
        "dataset_variant_count": len(items),
        "dataset_group_count": len({str(item.metadata["group_id"]) for item in items}),
        "failed_variant_count": sum(
            result_by_id[item.task_id].get("score") is None for item in items
        ),
        "excluded_group_count": len(excluded_groups),
        "excluded_groups": [excluded_groups[key] for key in sorted(excluded_groups)],
        "evaluation_protocol": (
            "Each independent transformation is paired with its original class; "
            "a response is correct when the direction-normalized readability "
            "score decreases. Raw LLOC is negated before paired aggregation. "
            "If a method fails on any member of a group, the entire group is "
            "excluded and reported explicitly."
        ),
    }
    output_path = summary_path.parent / "paired_summary.json"
    output_path.write_text(
        json.dumps(paired_summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    overall = paired_summary["overall"]
    print(
        f"{args.method} on {args.dataset}: "
        f"groups={paired_summary['group_count']}/"
        f"{paired_summary['dataset_group_count']}, "
        f"decrease={overall['score_decrease_rate']:.4f}, "
        f"changed_only={overall['changed_only_score_decrease_rate']:.4f}, "
        f"mean_drop={overall['mean_original_minus_variant']:.6f}",
        flush=True,
    )
    print(f"Wrote {output_path}", flush=True)


def failed_groups(
    items: list[Any],
    result_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    failures: dict[str, dict[str, Any]] = {}
    for item in items:
        result = result_by_id[item.task_id]
        if result.get("score") is not None:
            continue
        group_id = str(item.metadata["group_id"])
        entry = failures.setdefault(
            group_id,
            {
                "group_id": group_id,
                "source": str(item.metadata.get("source", "")),
                "unit_name": str(item.metadata.get("unit_name", "")),
                "failed_variants": [],
            },
        )
        entry["failed_variants"].append(
            {
                "task_id": item.task_id,
                "stage": str(item.metadata.get("stage", "")),
                "error": str(result.get("error", "missing score")),
            }
        )
    return failures


def paired_row(
    result: dict[str, Any],
    metadata: dict[str, Any],
    *,
    method: str,
) -> dict[str, Any]:
    if result.get("score") is None:
        raise ValueError(
            f"Method failed for {result.get('task_id')}: {result.get('error', 'no score')}"
        )
    raw_score = float(result["score"])
    readability_score = -raw_score if method == "lloc" else raw_score
    return {
        "task_id": str(result["task_id"]),
        "group_id": str(metadata["group_id"]),
        "source": str(metadata["source"]),
        "unit_name": str(metadata.get("unit_name", "")),
        "position": int(metadata.get("order", metadata["level"])),
        "stage": str(metadata["stage"]),
        "interference": metadata.get("interference"),
        "category": metadata.get("category"),
        "is_baseline": bool(metadata["is_baseline_variant"]),
        "score": readability_score,
        "raw_method_score": raw_score,
        "content_sha256": str(metadata["content_sha256"]),
    }


if __name__ == "__main__":
    main()
