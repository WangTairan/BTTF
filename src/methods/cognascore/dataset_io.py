"""Shared dataset loading helpers for CognaScore production and experiments."""

import hashlib
from pathlib import Path

from src.datasets import DatasetItem, load_code_dataset
from src.experiments.paths import dataset_name_for_path


def load_items(path: Path) -> list[DatasetItem]:
    return load_code_dataset(path)


def dataset_output_name(path: Path) -> str:
    return dataset_name_for_path(path)


def item_source_sha256(item: DatasetItem) -> str:
    """Return and validate the stable source fingerprint for one dataset item."""
    calculated = hashlib.sha256(item.content.encode("utf-8")).hexdigest()
    declared = item.metadata.get("content_sha256")
    if declared is not None and str(declared) != calculated:
        raise ValueError(
            f"Source hash mismatch for {item.task_id}: "
            f"metadata={declared}, calculated={calculated}"
        )
    return calculated
