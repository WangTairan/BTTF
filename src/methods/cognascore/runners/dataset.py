from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from src.experiments.progress import DatasetProgress

from ..visualization import write_visualization
from .common import (
    add_scoring_args,
    build_scorer,
    configured_output_dir,
    dataset_output_name,
    load_items,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CognaScore over a project dataset.")
    parser.add_argument("dataset", type=Path, help="Supported Java/code dataset path or directory.")
    add_scoring_args(parser)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-errors", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = load_items(args.dataset)
    if args.limit is not None:
        items = items[: args.limit]
    name = dataset_output_name(args.dataset)
    result_dir = configured_output_dir(args, name)
    result_dir.mkdir(parents=True, exist_ok=True)
    scorer = build_scorer(args)
    records = []
    errors = []
    progress = DatasetProgress(len(items))
    for index, item in enumerate(items, start=1):
        progress.running(index, item.task_id)
        try:
            record = scorer.process(item.content, task_id=item.task_id)
            record = replace(record, metadata={**record.metadata, **item.metadata})
            records.append(record)
        except Exception as exc:
            if not args.skip_errors:
                raise
            errors.append({"task_id": item.task_id, "error": repr(exc)})
    description = (
        f"model={args.embedding_model}, DBSCAN eps={args.eps}, minPts={args.min_pts}"
    )
    write_visualization(result_dir / "visualization", dataset=name, description=description, records=records)
    manifest = {
        "meta": {
            "dataset": str(args.dataset),
            "description": description,
            "embedding_model": args.embedding_model,
            "dbscan": {
                "eps": args.eps,
                "min_pts": args.min_pts,
            },
            "record_count": len(records),
            "error_count": len(errors),
        },
        "records": [
            {"task_id": record.task_id, "score": record.avg_diameter}
            for record in records
        ],
        "errors": errors,
    }
    manifest_path = result_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}", flush=True)
    print(f"Wrote {result_dir / 'visualization' / 'visualize.html'}", flush=True)


if __name__ == "__main__":
    main()
