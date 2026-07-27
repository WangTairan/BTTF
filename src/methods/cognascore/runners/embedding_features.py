from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

if not os.environ.get("LOKY_MAX_CPU_COUNT"):
    os.environ["LOKY_MAX_CPU_COUNT"] = str(max((os.cpu_count() or 2) - 1, 1))

from src.experiments.paths import output_dir
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from ..embedding_cache import EmbeddingCache, embedding_cache_path
from ..embedding_features import extract_embedding_feature_row, write_embedding_feature_database
from ..results import model_slug
from .common import dataset_output_name, load_items


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build embedding-derived CognaScore feature tables.")
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Dataset paths. Defaults to all current code datasets.",
    )
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--embedding-cache-root", type=Path, default=Path("output/cognascore_embeddings"))
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output root. Defaults to output/cognascore_embedding_features/.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--min-coverage", type=float, default=0.0)
    parser.add_argument(
        "--max-vectors-per-task",
        type=int,
        default=512,
        help="Deterministically cap unique vectors per task for expensive embedding algorithms.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse an existing feature CSV with the current schema and checkpoint progress while computing missing rows.",
    )
    parser.add_argument(
        "--update-incomplete",
        action="store_true",
        help="With --resume, recompute existing rows whose embedding coverage is below 1.0 or whose source count is 0.",
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="With --resume, recompute every selected task while preserving checkpoint/resume behavior.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        help="With --resume, write the CSV/metadata after this many newly computed rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.exists():
        raise SystemExit(f"Missing embedding cache: {cache_path}")

    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        for path in dataset_paths:
            dataset_name = dataset_output_name(path)
            all_items = load_items(path)
            items = all_items
            if args.limit is not None:
                items = all_items[: args.limit]
            feature_dir = output_dir(
                args.output,
                "cognascore_embedding_features",
                dataset_name,
                model_slug(args.embedding_model),
            )
            base_metadata = {
                "dataset": dataset_name,
                "dataset_path": str(path),
                "embedding_model": args.embedding_model,
                "embedding_cache": str(cache_path),
                "min_coverage": args.min_coverage,
                "max_vectors_per_task": args.max_vectors_per_task,
                "resume": bool(args.resume),
                "update_incomplete": bool(args.update_incomplete),
                "update_all": bool(args.update_all),
            }
            rows_by_task: dict[str, dict] = {}
            if args.resume:
                rows_by_task = _load_existing_rows(feature_dir)
                if rows_by_task:
                    print(f"Loaded {len(rows_by_task)} existing feature rows for {dataset_name}", flush=True)
            rows = []
            skipped = []
            computed_since_checkpoint = 0
            for index, item in enumerate(items, start=1):
                if args.resume and item.task_id in rows_by_task and not _should_update_existing(
                    rows_by_task[item.task_id],
                    update_incomplete=args.update_incomplete,
                    update_all=args.update_all,
                ):
                    print(f"[{index}/{len(items)}] Reusing embedding features for {dataset_name} {item.task_id}", flush=True)
                    continue
                print(f"[{index}/{len(items)}] Embedding features for {dataset_name} {item.task_id}", flush=True)
                total_count, available_count = cache.task_source_counts(dataset_name, item.task_id)
                coverage = available_count / max(total_count, 1)
                if coverage < args.min_coverage:
                    skipped.append({"task_id": item.task_id, "coverage": coverage})
                    continue
                vector_rows = cache.task_vectors(dataset_name, item.task_id)
                rows.append(
                    extract_embedding_feature_row(
                        dataset=dataset_name,
                        task_id=item.task_id,
                        readability_score=item.readability_score,
                        total_source_count=total_count,
                        vector_rows=vector_rows,
                        max_vectors=args.max_vectors_per_task,
                    )
                )
                row = rows[-1]
                if args.resume:
                    rows_by_task[item.task_id] = row
                    computed_since_checkpoint += 1
                    if computed_since_checkpoint >= max(args.checkpoint_every, 1):
                        _write_checkpoint(
                            rows_by_task,
                            items=all_items,
                            output_dir=feature_dir,
                            metadata={**base_metadata, "skipped_count": len(skipped), "skipped": skipped},
                        )
                        computed_since_checkpoint = 0
            if args.resume:
                rows = _ordered_existing_rows(rows_by_task, items=all_items)
            csv_path, metadata_path = write_embedding_feature_database(
                rows=rows,
                output_dir=feature_dir,
                metadata={
                    **base_metadata,
                    "skipped_count": len(skipped),
                    "skipped": skipped,
                },
            )
            print(f"Wrote {csv_path}", flush=True)
            print(f"Wrote {metadata_path}", flush=True)


def _load_existing_rows(feature_dir: Path) -> dict[str, dict]:
    csv_path = feature_dir / "features.csv"
    if not csv_path.exists():
        return {}
    expected_columns = ["dataset", "task_id", "readability_score", *extract_embedding_feature_columns()]
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if columns != expected_columns:
            raise SystemExit(
                f"Cannot resume from {csv_path}: schema mismatch. "
                "Regenerate without --resume or move the old feature table."
            )
        return {str(row["task_id"]): dict(row) for row in reader}


def extract_embedding_feature_columns() -> list[str]:
    from ..embedding_features import embedding_feature_names

    return embedding_feature_names()


def _should_update_existing(row: dict, *, update_incomplete: bool, update_all: bool) -> bool:
    if update_all:
        return True
    if not update_incomplete:
        return False
    return _as_float(row.get("embedding_coverage_ratio")) < 1.0 or _as_float(row.get("embedding_source_count")) <= 0.0


def _as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _ordered_existing_rows(rows_by_task: dict[str, dict], *, items) -> list[dict]:
    return [rows_by_task[item.task_id] for item in items if item.task_id in rows_by_task]


def _write_checkpoint(rows_by_task: dict[str, dict], *, items, output_dir: Path, metadata: dict) -> None:
    csv_path, metadata_path = write_embedding_feature_database(
        rows=_ordered_existing_rows(rows_by_task, items=items),
        output_dir=output_dir,
        metadata={
            **metadata,
            "checkpoint": True,
            "completed_count": len(rows_by_task),
        },
    )
    print(f"Checkpointed {len(rows_by_task)} rows to {csv_path}", flush=True)
    print(f"Checkpointed metadata to {metadata_path}", flush=True)


if __name__ == "__main__":
    main()
