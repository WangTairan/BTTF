"""Shared dataset loading helpers for CognaScore production and experiments."""

from pathlib import Path

from src.datasets import DatasetItem, load_code_dataset
from src.experiments.paths import dataset_name_for_path


def load_items(path: Path) -> list[DatasetItem]:
    return load_code_dataset(path)


def dataset_output_name(path: Path) -> str:
    return dataset_name_for_path(path)
