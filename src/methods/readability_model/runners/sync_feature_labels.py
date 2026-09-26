"""Synchronize feature-table targets from the canonical dataset adapter.

Feature values do not depend on readability labels. This runner updates only
the identity/target column after a dataset label-policy change, validates exact
task coverage, and leaves embedding vectors and derived feature values intact.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.methods.readability_model.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_name = dataset_name_for_path(args.dataset)
    items = load_code_dataset(args.dataset)
    labels = {
        item.task_id: float(item.readability_score)
        for item in items
        if item.readability_score is not None
    }
    if len(labels) != len(items):
        raise ValueError(
            f"Dataset {dataset_name} has {len(items) - len(labels)} rows without labels"
        )

    tables = sorted((args.base_root / dataset_name).glob("*/features.csv"))
    tables += sorted((args.embedding_root / dataset_name).glob("*/features.csv"))
    if not tables:
        raise FileNotFoundError(f"No feature tables found for {dataset_name}")
    for table in tables:
        sync_table(table, labels, dataset_name)
        print(f"Updated {table}", flush=True)


def sync_table(path: Path, labels: dict[str, float], dataset_name: str) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if not fieldnames or "task_id" not in fieldnames or "readability_score" not in fieldnames:
            raise ValueError(f"Missing identity columns in {path}")
        rows = list(reader)

    task_ids = [row["task_id"] for row in rows]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError(f"Duplicate task IDs in {path}")
    table_ids = set(task_ids)
    label_ids = set(labels)
    if table_ids != label_ids:
        raise ValueError(
            f"Task coverage mismatch in {path}: "
            f"missing={sorted(label_ids - table_ids)[:5]}, "
            f"unknown={sorted(table_ids - label_ids)[:5]}"
        )
    for row in rows:
        row["readability_score"] = repr(labels[row["task_id"]])

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)

    metadata_path = path.with_name("metadata.json")
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["label_sync"] = {
            "dataset": dataset_name,
            "row_count": len(rows),
            "source": "canonical_dataset_adapter",
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        temporary_metadata = metadata_path.with_suffix(".json.tmp")
        temporary_metadata.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_metadata, metadata_path)


if __name__ == "__main__":
    main()
