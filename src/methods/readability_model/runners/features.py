from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.experiments.registry import READABILITY_MODEL_DEFAULT_EMBEDDING

from ..feature_database import (
    BASE_FEATURE_BUILD_VERSION,
    extract_feature_row,
    write_feature_database,
)
from ..dataset_io import item_source_sha256
from ..paths import BASE_FEATURE_ROOT
from ..results import model_slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the model-independent feature table.")
    parser.add_argument("dataset", type=Path, help="Supported code dataset path or directory.")
    parser.add_argument(
        "--embedding-model",
        action="append",
        dest="embedding_models",
        help=(
            "Embedding-model namespace receiving this model-independent base table. "
            "Repeat the option to write several namespaces without re-extracting features."
        ),
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Reuse current-schema rows whose source SHA-256 is unchanged. "
            "Rows with identical source hashes may be reused across task IDs."
        ),
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Ignore any existing table and rebuild every selected row.",
    )
    parser.add_argument(
        "--quiet-reuse",
        action="store_true",
        help="Suppress one-line logs for rows reused by the incremental updater.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=BASE_FEATURE_ROOT,
        help="Base-feature root. Defaults to artifacts/cognascore/features/base/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_name = dataset_name_for_path(args.dataset)
    items = load_code_dataset(args.dataset)
    if args.limit is not None:
        items = items[: args.limit]

    embedding_models = args.embedding_models or [READABILITY_MODEL_DEFAULT_EMBEDDING]
    source_hashes = {item.task_id: item_source_sha256(item) for item in items}
    reusable_rows, reusable_hashes = _load_reusable_rows(
        args.output,
        dataset_name,
        embedding_models,
        items,
        resume=args.resume and not args.replace_existing,
    )
    rows_by_hash = {
        reusable_hashes[task_id]: row
        for task_id, row in reusable_rows.items()
        if task_id in reusable_hashes
    }
    rows = []
    extracted_count = 0
    reused_task_count = 0
    reused_hash_count = 0
    for index, item in enumerate(items, start=1):
        source_hash = source_hashes[item.task_id]
        exact = reusable_rows.get(item.task_id)
        exact_hash = reusable_hashes.get(item.task_id)
        if exact is not None and exact_hash == source_hash:
            row = _clone_identity(exact, dataset_name, item)
            reused_task_count += 1
            action = "Reusing unchanged"
        elif source_hash in rows_by_hash:
            row = _clone_identity(rows_by_hash[source_hash], dataset_name, item)
            reused_hash_count += 1
            action = "Reusing identical-source"
        else:
            row = extract_feature_row(dataset=dataset_name, item=item)
            rows_by_hash[source_hash] = row
            extracted_count += 1
            action = "Extracting"
        if not args.quiet_reuse or action == "Extracting":
            print(f"[{index}/{len(items)}] {action} features for {item.task_id}", flush=True)
        rows.append(row)

    for embedding_model in embedding_models:
        feature_dir = args.output / dataset_name / model_slug(embedding_model)
        csv_path, metadata_path = write_feature_database(
            rows=rows,
            output_dir=feature_dir,
            metadata={
                "dataset": dataset_name,
                "dataset_path": str(args.dataset),
                "embedding_model_namespace": embedding_model,
                "source": "direct_chunk_and_code_extraction",
                "model_independent": True,
                "base_feature_build_version": BASE_FEATURE_BUILD_VERSION,
                "incremental_resume": bool(args.resume and not args.replace_existing),
                "source_sha256_by_task": source_hashes,
                "extracted_count": extracted_count,
                "reused_unchanged_task_count": reused_task_count,
                "reused_identical_source_count": reused_hash_count,
            },
        )
        print(f"Wrote {csv_path}", flush=True)
        print(f"Wrote {metadata_path}", flush=True)
    print(
        "Base-feature update: "
        f"extracted={extracted_count}, "
        f"reused_unchanged_task={reused_task_count}, "
        f"reused_identical_source={reused_hash_count}, "
        f"retired={max(len(reusable_rows) - reused_task_count, 0)}",
        flush=True,
    )


def _load_reusable_rows(
    output_root: Path,
    dataset_name: str,
    embedding_models: list[str],
    items,
    *,
    resume: bool,
) -> tuple[dict[str, dict], dict[str, str]]:
    if not resume:
        return {}, {}
    candidates = [
        output_root / dataset_name / model_slug(model)
        for model in embedding_models
    ]
    feature_dir = next(
        (path for path in candidates if (path / "features.csv").is_file()),
        None,
    )
    if feature_dir is None:
        return {}, {}
    csv_path = feature_dir / "features.csv"
    metadata_path = feature_dir / "metadata.json"
    if not metadata_path.is_file():
        print(f"Ignoring {csv_path}: missing metadata.json", flush=True)
        return {}, {}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    existing_version = metadata.get("base_feature_build_version")
    if existing_version != BASE_FEATURE_BUILD_VERSION:
        print(
            f"Rebuilding {csv_path}: base-feature build version "
            f"{existing_version!r} -> {BASE_FEATURE_BUILD_VERSION}",
            flush=True,
        )
        return {}, {}
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        rows = {str(row["task_id"]): dict(row) for row in csv.DictReader(handle)}
    stored_hashes = {
        str(task_id): str(source_hash)
        for task_id, source_hash in metadata.get("source_sha256_by_task", {}).items()
    }
    if not stored_hashes:
        # One-time migration for tables produced before source fingerprints were
        # recorded. Constructed variant IDs are immutable; matching current IDs
        # therefore provide safe anchors for subsequent hash-based reuse.
        if all(item.metadata.get("content_sha256") for item in items):
            current = {item.task_id: item_source_sha256(item) for item in items}
            stored_hashes = {
                task_id: current[task_id]
                for task_id in rows.keys() & current.keys()
            }
            print(
                f"Bootstrapped {len(stored_hashes)} source hashes from unchanged task IDs in {csv_path}",
                flush=True,
            )
        else:
            print(
                f"Cannot bootstrap source hashes for {csv_path}: dataset items do not "
                "provide manifest-validated content_sha256 values; rebuilding rows.",
                flush=True,
            )
    return rows, stored_hashes


def _clone_identity(row: dict, dataset_name: str, item) -> dict:
    cloned = dict(row)
    cloned["dataset"] = dataset_name
    cloned["task_id"] = item.task_id
    cloned["readability_score"] = item.readability_score
    return cloned


if __name__ == "__main__":
    main()
