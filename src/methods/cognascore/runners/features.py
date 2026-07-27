from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.experiments.paths import output_dir
from src.experiments.registry import COGNASCORE_DEFAULT_CACHE_DIR, COGNASCORE_DEFAULT_MODEL

from ..feature_database import extract_feature_row, write_feature_database
from ..results import model_slug
from .common import (
    dataset_output_name,
    load_items,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a stable CognaScore feature database.")
    parser.add_argument("dataset", type=Path, help="Supported code dataset path or directory.")
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--models", type=Path, default=COGNASCORE_DEFAULT_CACHE_DIR)
    parser.add_argument("--eps", type=float, default=0.18)
    parser.add_argument("--min-pts", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default=None, help="cpu, cuda, mps, or auto.")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--cognascore-output-root",
        type=Path,
        default=Path("output/cognascore"),
        help="Root containing existing CognaScore summary.json files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Feature database output root. Defaults to output/cognascore_features/.",
    )
    parser.add_argument(
        "--run-missing",
        action="store_true",
        help="Run CognaScore for items missing from the existing summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_name = dataset_output_name(args.dataset)
    items = load_items(args.dataset)
    if args.limit is not None:
        items = items[: args.limit]

    summary_path = args.cognascore_output_root / dataset_name / model_slug(args.embedding_model) / "summary.json"
    stored_results = _load_summary_results(summary_path)
    scorer = None
    rows = []
    errors = []
    for index, item in enumerate(items, start=1):
        print(f"[{index}/{len(items)}] Extracting features for {item.task_id}", flush=True)
        result = stored_results.get(item.task_id)
        if result is None:
            if not args.run_missing:
                errors.append({"task_id": item.task_id, "error": "missing CognaScore result"})
                continue
            if scorer is None:
                from ..method import CognaScoreScorer

                scorer = CognaScoreScorer(
                    model_name=args.embedding_model,
                    eps=args.eps,
                    min_pts=args.min_pts,
                    batch_size=args.batch_size,
                    device=args.device,
                    cache_dir=args.models,
                )
            result = scorer.score(item.content).__dict__
        rows.append(
            extract_feature_row(
                dataset=dataset_name,
                item=item,
                cognascore_result=result,
            )
        )

    feature_dir = output_dir(
        args.output,
        "cognascore_features",
        dataset_name,
        model_slug(args.embedding_model),
    )
    csv_path, metadata_path = write_feature_database(
        rows=rows,
        output_dir=feature_dir,
        metadata={
            "dataset": dataset_name,
            "dataset_path": str(args.dataset),
            "embedding_model": args.embedding_model,
            "dbscan": {"eps": args.eps, "min_pts": args.min_pts},
            "source_summary": str(summary_path),
            "run_missing": args.run_missing,
            "error_count": len(errors),
            "errors": errors,
        },
    )
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {metadata_path}", flush=True)


def _load_summary_results(summary_path: Path) -> dict[str, dict[str, Any]]:
    if not summary_path.exists():
        return {}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    results: dict[str, dict[str, Any]] = {}
    for row in summary.get("results", []):
        task_id = row.get("task_id")
        if not task_id:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            results[str(task_id)] = result
    return results


if __name__ == "__main__":
    main()
