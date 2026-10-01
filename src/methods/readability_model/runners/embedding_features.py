from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

if not os.environ.get("LOKY_MAX_CPU_COUNT"):
    os.environ["LOKY_MAX_CPU_COUNT"] = str(max((os.cpu_count() or 2) - 1, 1))

from src.experiments.registry import DATASETS, READABILITY_MODEL_DEFAULT_EMBEDDING

from ..comment_relevance import calibrate_comment_relevance
from ..embedding_cache import EmbeddingCache, embedding_cache_path
from ..embedding_features import (
    EMBEDDING_FEATURE_BUILD_VERSION,
    embedding_feature_names,
    extract_embedding_feature_row,
    write_embedding_feature_database,
)
from ..extractors import extractor_for_language
from ..results import model_slug
from ..semantic_context import (
    APPLICATION_ANCHOR_TASK,
    MATH_ANCHOR_TASK,
    WHOLE_CODE_CONTEXT_TYPE,
    context_anchor_groups,
    centroid,
)
from ..dataset_io import dataset_output_name, item_source_sha256, load_items
from ..paths import CALIBRATION_ROOT, EMBEDDING_CACHE_ROOT, EMBEDDING_FEATURE_ROOT


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build embedding-derived readability features.")
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Dataset paths. Defaults to all current code datasets.",
    )
    parser.add_argument("--embedding-model", default=READABILITY_MODEL_DEFAULT_EMBEDDING)
    parser.add_argument("--embedding-cache-root", type=Path, default=EMBEDDING_CACHE_ROOT)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EMBEDDING_FEATURE_ROOT,
        help=(
            "Embedding-feature root. Defaults to "
            "artifacts/cognascore/features/embedding/."
        ),
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=1.0,
        help="Required embedded-source coverage per task. Defaults to 1.0; incomplete caches fail loudly.",
    )
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
        help="With --resume, recompute existing rows containing a missing current-schema feature value.",
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="With --resume, recompute every selected task while preserving checkpoint/resume behavior.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete an existing feature table before rebuilding. Useful after schema changes.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        help="With --resume, write the CSV/metadata after this many newly computed rows.",
    )
    parser.add_argument(
        "--quiet-reuse",
        action="store_true",
        help="Suppress one-line logs for rows reused by source hash.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.exists():
        raise SystemExit(f"Missing embedding cache: {cache_path}")

    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        context_centroids = _load_context_centroids(cache)
        try:
            comment_calibration = calibrate_comment_relevance(cache)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        calibration_path = _write_comment_relevance_calibration(
            args.embedding_model,
            comment_calibration.as_metadata(),
        )
        print(
            "Comment-relevance calibration: "
            f"threshold={comment_calibration.threshold:.6f}, "
            "leave-one-anchor-out balanced accuracy="
            f"{comment_calibration.leave_one_anchor_out_balanced_accuracy:.4f}",
            flush=True,
        )
        for path in dataset_paths:
            dataset_name = dataset_output_name(path)
            all_items = load_items(path)
            items = all_items
            if args.limit is not None:
                items = all_items[: args.limit]
            feature_dir = args.output / dataset_name / model_slug(args.embedding_model)
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
                "replace_existing": bool(args.replace_existing),
                "embedding_feature_build_version": EMBEDDING_FEATURE_BUILD_VERSION,
                "comment_relevance_calibration": {
                    **comment_calibration.as_metadata(),
                    "artifact": str(calibration_path),
                },
            }
            rows_by_task: dict[str, dict] = {}
            stored_hashes: dict[str, str] = {}
            if args.replace_existing:
                _delete_existing_table(feature_dir)
            if args.resume:
                rows_by_task, stored_hashes = _load_existing_rows(feature_dir)
                if rows_by_task:
                    print(f"Loaded {len(rows_by_task)} existing feature rows for {dataset_name}", flush=True)
            source_hashes = {
                item.task_id: item_source_sha256(item)
                for item in all_items
            }
            if rows_by_task and not stored_hashes:
                if all(item.metadata.get("content_sha256") for item in all_items):
                    stored_hashes = {
                        item.task_id: source_hashes[item.task_id]
                        for item in all_items
                        if item.task_id in rows_by_task
                    }
                    print(
                        f"Bootstrapped {len(stored_hashes)} embedding-feature source hashes "
                        "from unchanged task IDs",
                        flush=True,
                    )
                else:
                    print(
                        "Existing embedding-feature metadata has no source hashes and "
                        "the dataset has no manifest-validated content hashes; "
                        "recomputing selected rows.",
                        flush=True,
                    )
            rows_by_hash = {
                stored_hashes[task_id]: row
                for task_id, row in rows_by_task.items()
                if task_id in stored_hashes
            }
            rows = []
            skipped = []
            computed_since_checkpoint = 0
            computed_count = 0
            reused_task_count = 0
            reused_hash_count = 0
            for index, item in enumerate(items, start=1):
                source_hash = source_hashes[item.task_id]
                existing = rows_by_task.get(item.task_id)
                existing_hash = stored_hashes.get(item.task_id)
                if (
                    args.resume
                    and existing is not None
                    and existing_hash == source_hash
                    and not _should_update_existing(
                        existing,
                        update_incomplete=args.update_incomplete,
                        update_all=args.update_all,
                    )
                ):
                    if not args.quiet_reuse:
                        print(f"[{index}/{len(items)}] Reusing embedding features for {dataset_name} {item.task_id}", flush=True)
                    reused_task_count += 1
                    continue
                hash_match = rows_by_hash.get(source_hash)
                if (
                    args.resume
                    and hash_match is not None
                    and not _should_update_existing(
                        hash_match,
                        update_incomplete=args.update_incomplete,
                        update_all=args.update_all,
                    )
                ):
                    if not args.quiet_reuse:
                        print(
                            f"[{index}/{len(items)}] Reusing identical-source embedding features "
                            f"for {dataset_name} {item.task_id}",
                            flush=True,
                        )
                    row = _clone_embedding_identity(hash_match, dataset_name, item)
                    rows_by_task[item.task_id] = row
                    stored_hashes[item.task_id] = source_hash
                    reused_hash_count += 1
                    continue
                print(f"[{index}/{len(items)}] Embedding features for {dataset_name} {item.task_id}", flush=True)
                total_count, available_count = cache.task_source_counts(
                    dataset_name,
                    item.task_id,
                    exclude_chunk_types=(WHOLE_CODE_CONTEXT_TYPE,),
                )
                coverage = available_count / max(total_count, 1)
                if total_count == 0:
                    extracted_chunks, _ = extractor_for_language(
                        item.metadata.get("language"),
                        allow_fragments=item.metadata.get("source_form") == "snippet",
                    ).extract_with_member_fallback(item.content)
                    if extracted_chunks:
                        raise SystemExit(
                            f"No embedding source references for {dataset_name} {item.task_id}, "
                            f"but the extractor produced {len(extracted_chunks)} chunks. "
                            "Run the embeddings runner successfully before deriving features."
                        )
                    coverage = 1.0
                if coverage < args.min_coverage:
                    raise SystemExit(
                        f"Incomplete embedding cache for {dataset_name} {item.task_id}: "
                        f"coverage={coverage:.6f} ({available_count}/{total_count}), "
                        f"required={args.min_coverage:.6f}."
                    )
                vector_rows = cache.task_vectors(
                    dataset_name,
                    item.task_id,
                    exclude_chunk_types=(WHOLE_CODE_CONTEXT_TYPE,),
                )
                code_segment_vectors = cache.task_vectors_for_chunk_type(dataset_name, item.task_id, WHOLE_CODE_CONTEXT_TYPE)
                if not code_segment_vectors:
                    raise SystemExit(
                        f"Missing whole-code context embedding for {dataset_name} {item.task_id}. "
                        "Run the embeddings runner successfully before deriving features."
                    )
                code_vector = code_segment_vectors[0][1] if code_segment_vectors else None
                rows.append(
                    extract_embedding_feature_row(
                        dataset=dataset_name,
                        task_id=item.task_id,
                        readability_score=item.readability_score,
                        total_source_count=total_count,
                        vector_rows=vector_rows,
                        code_vector=code_vector,
                        code_segment_vectors=code_segment_vectors,
                        math_centroid=context_centroids[MATH_ANCHOR_TASK],
                        application_centroid=context_centroids[APPLICATION_ANCHOR_TASK],
                        comment_relevance_threshold=comment_calibration.threshold,
                        max_vectors=args.max_vectors_per_task,
                    )
                )
                row = rows[-1]
                rows_by_hash[source_hash] = row
                stored_hashes[item.task_id] = source_hash
                computed_count += 1
                if args.resume:
                    rows_by_task[item.task_id] = row
                    computed_since_checkpoint += 1
                    if computed_since_checkpoint >= max(args.checkpoint_every, 1):
                        _write_checkpoint(
                            rows_by_task,
                            items=all_items,
                            output_dir=feature_dir,
                            metadata={
                                **base_metadata,
                                "source_sha256_by_task": source_hashes,
                                "skipped_count": len(skipped),
                                "skipped": skipped,
                            },
                        )
                        computed_since_checkpoint = 0
            if args.resume:
                rows = _ordered_existing_rows(rows_by_task, items=all_items)
            csv_path, metadata_path = write_embedding_feature_database(
                rows=rows,
                output_dir=feature_dir,
                metadata={
                    **base_metadata,
                    "source_sha256_by_task": source_hashes,
                    "computed_count": computed_count,
                    "reused_unchanged_task_count": reused_task_count,
                    "reused_identical_source_count": reused_hash_count,
                    "skipped_count": len(skipped),
                    "skipped": skipped,
                },
            )
            print(f"Wrote {csv_path}", flush=True)
            print(f"Wrote {metadata_path}", flush=True)
            print(
                "Embedding-feature update: "
                f"computed={computed_count}, "
                f"reused_unchanged_task={reused_task_count}, "
                f"reused_identical_source={reused_hash_count}, "
                f"retired={len(set(rows_by_task) - set(source_hashes))}",
                flush=True,
            )


def _load_existing_rows(feature_dir: Path) -> tuple[dict[str, dict], dict[str, str]]:
    csv_path = feature_dir / "features.csv"
    if not csv_path.exists():
        return {}, {}
    metadata_path = feature_dir / "metadata.json"
    if not metadata_path.exists():
        print(f"Ignoring {csv_path}: missing metadata.json", flush=True)
        return {}, {}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    existing_version = metadata.get("embedding_feature_build_version")
    if existing_version != EMBEDDING_FEATURE_BUILD_VERSION:
        print(
            f"Rebuilding {csv_path}: embedding-feature build version "
            f"{existing_version!r} -> {EMBEDDING_FEATURE_BUILD_VERSION}",
            flush=True,
        )
        return {}, {}
    expected_columns = ["dataset", "task_id", "readability_score", *extract_embedding_feature_columns()]
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if columns != expected_columns:
            raise SystemExit(
                f"Cannot resume from {csv_path}: schema mismatch. "
                "Regenerate without --resume or move the old feature table."
            )
        rows = {str(row["task_id"]): dict(row) for row in reader}
    source_hashes = {
        str(task_id): str(source_hash)
        for task_id, source_hash in metadata.get("source_sha256_by_task", {}).items()
    }
    return rows, source_hashes


def _clone_embedding_identity(row: dict, dataset_name: str, item) -> dict:
    cloned = dict(row)
    cloned["dataset"] = dataset_name
    cloned["task_id"] = item.task_id
    cloned["readability_score"] = item.readability_score
    return cloned


def _write_comment_relevance_calibration(
    embedding_model: str,
    calibration: dict,
) -> Path:
    output_dir = CALIBRATION_ROOT / model_slug(embedding_model)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "comment_relevance.json"
    payload = {
        "embedding_model": embedding_model,
        "pooling": "attention-mask mean pooling",
        "score_definition": (
            "maximum cosine similarity between one comment embedding and any "
            "normalized non-comment semantic-chunk embedding"
        ),
        "threshold_selection": (
            "maximize balanced accuracy on the independent calibration anchors; "
            "use the median of tied optimal thresholds"
        ),
        **calibration,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _delete_existing_table(feature_dir: Path) -> None:
    for filename in ("features.csv", "metadata.json"):
        path = feature_dir / filename
        if path.exists():
            path.unlink()


def extract_embedding_feature_columns() -> list[str]:
    from ..embedding_features import embedding_feature_names

    return embedding_feature_names()


def _load_context_centroids(cache: EmbeddingCache) -> dict[str, object]:
    centroids = {}
    missing = []
    for task_id, anchors in context_anchor_groups().items():
        by_text = cache.vectors_for_texts([anchor.code for anchor in anchors])
        vectors = []
        for anchor in anchors:
            vector = by_text.get(anchor.code)
            if vector is None:
                missing.append(f"{task_id}:{anchor.name}")
            else:
                vectors.append(vector)
        centroids[task_id] = centroid(vectors)
    if missing:
        raise SystemExit(
            "Missing semantic-context anchor embeddings. Run the embeddings runner first. "
            f"Missing anchors: {', '.join(missing[:10])}"
        )
    return centroids


def _should_update_existing(row: dict, *, update_incomplete: bool, update_all: bool) -> bool:
    if update_all:
        return True
    if not update_incomplete:
        return False
    return any(row.get(name) in (None, "") for name in embedding_feature_names())


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
