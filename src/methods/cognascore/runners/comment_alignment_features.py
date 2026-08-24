from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from ..dataset_io import dataset_output_name, load_items
from ..embedding_cache import EmbeddingCache, embedding_cache_path
from ..embedding_features import (
    _comment_identifier_alignment_features,
    embedding_feature_names,
    write_embedding_feature_database,
)
from ..paths import EMBEDDING_CACHE_ROOT, EMBEDDING_FEATURE_ROOT
from ..results import model_slug
from ..semantic_context import WHOLE_CODE_CONTEXT_TYPE
from ..semantic_context import short_identifier_candidate_ratio


ALIGNMENT_FEATURE_NAMES = (
    "scalabrino_comment_embedding_coverage_ratio",
    "scalabrino_comment_identifier_cosine_mean",
    "scalabrino_comment_identifier_cosine_max",
    "scalabrino_comment_identifier_centroid_cosine",
)
INCREMENTAL_FEATURE_NAMES = (
    *ALIGNMENT_FEATURE_NAMES,
    "short_identifier_candidate_ratio",
)
LEGACY_ALIGNMENT_NAMES = {
    "comment_embedding_coverage_ratio": "scalabrino_comment_embedding_coverage_ratio",
    "comment_identifier_cosine_mean": "scalabrino_comment_identifier_cosine_mean",
    "comment_identifier_cosine_max": "scalabrino_comment_identifier_cosine_max",
    "comment_identifier_centroid_cosine": "scalabrino_comment_identifier_centroid_cosine",
}
DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append comment-identifier alignment features to existing embedding-feature "
            "tables without recomputing embedding geometry or clustering."
        )
    )
    parser.add_argument("datasets", nargs="*", type=Path)
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--embedding-cache-root", type=Path, default=EMBEDDING_CACHE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--max-vectors-per-type", type=int, default=512)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.exists():
        raise SystemExit(f"Missing embedding cache: {cache_path}")

    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        for dataset_path in dataset_paths:
            dataset = dataset_output_name(dataset_path)
            items = load_items(dataset_path)
            feature_dir = args.output / dataset / model_slug(args.embedding_model)
            rows_by_task, old_metadata = _load_legacy_table(feature_dir)
            expected_task_ids = {item.task_id for item in items}
            actual_task_ids = set(rows_by_task)
            if actual_task_ids != expected_task_ids:
                missing = sorted(expected_task_ids - actual_task_ids)
                extra = sorted(actual_task_ids - expected_task_ids)
                raise SystemExit(
                    f"Task mismatch in {feature_dir}: missing={missing[:5]}, extra={extra[:5]}. "
                    "Run the full embedding-feature builder instead."
                )

            for index, item in enumerate(items, start=1):
                total_count, available_count = cache.task_source_counts(
                    dataset,
                    item.task_id,
                    exclude_chunk_types=(WHOLE_CODE_CONTEXT_TYPE,),
                )
                if available_count != total_count:
                    raise SystemExit(
                        f"Incomplete embedding cache for {dataset} {item.task_id}: "
                        f"{available_count}/{total_count}."
                    )
                vector_rows = cache.task_vectors(
                    dataset,
                    item.task_id,
                    exclude_chunk_types=(WHOLE_CODE_CONTEXT_TYPE,),
                )
                rows_by_task[item.task_id].update(
                    _comment_identifier_alignment_features(
                        vector_rows,
                        total_source_count=total_count,
                        max_vectors_per_type=args.max_vectors_per_type,
                    )
                )
                identifier_lexemes = [
                    lexeme
                    for chunk_type, lexeme, _, _ in vector_rows
                    if chunk_type.upper() == "IDENTIFIER"
                ]
                rows_by_task[item.task_id]["short_identifier_candidate_ratio"] = (
                    short_identifier_candidate_ratio(identifier_lexemes)
                )
                if index % 100 == 0 or index == len(items):
                    print(f"[{index}/{len(items)}] Updated {dataset}", flush=True)

            rows = [rows_by_task[item.task_id] for item in items]
            csv_path, metadata_path = write_embedding_feature_database(
                rows=rows,
                output_dir=feature_dir,
                metadata={
                    **old_metadata,
                    "comment_identifier_alignment_incremental_update": True,
                    "comment_identifier_alignment_max_vectors_per_type": args.max_vectors_per_type,
                },
            )
            print(f"Wrote {csv_path}", flush=True)
            print(f"Wrote {metadata_path}", flush=True)


def _load_legacy_table(feature_dir: Path) -> tuple[dict[str, dict], dict]:
    csv_path = feature_dir / "features.csv"
    metadata_path = feature_dir / "metadata.json"
    if not csv_path.exists() or not metadata_path.exists():
        raise SystemExit(f"Missing existing embedding feature table under {feature_dir}")

    expected_columns = ["dataset", "task_id", "readability_score", *embedding_feature_names()]
    preceding_columns = [name for name in expected_columns if name not in INCREMENTAL_FEATURE_NAMES]
    missing_candidate_columns = [
        name for name in expected_columns if name != "short_identifier_candidate_ratio"
    ]
    old_prefixed_columns = [
        next((old for old, new in LEGACY_ALIGNMENT_NAMES.items() if new == name), name)
        for name in expected_columns
    ]
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_columns = reader.fieldnames or []
        if actual_columns not in (
            expected_columns,
            preceding_columns,
            missing_candidate_columns,
            old_prefixed_columns,
        ):
            raise SystemExit(
                f"Unexpected schema in {csv_path}. Expected the immediately preceding "
                "schema or the legacy unprefixed alignment schema."
            )
        rows = {}
        for row in reader:
            migrated = {
                LEGACY_ALIGNMENT_NAMES.get(name, name): value
                for name, value in row.items()
            }
            rows[str(migrated["task_id"])] = migrated

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return rows, metadata


if __name__ == "__main__":
    main()
