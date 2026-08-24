from pathlib import Path

from src.datasets.buse import load_dataset as load_buse_dataset
from src.datasets.code_jsonl import load_dataset as load_code_jsonl_dataset
from src.datasets.dorn import load_dataset as load_dorn_dataset
from src.datasets.jetbrains import load_dataset as load_jetbrains_dataset
from src.datasets.mbjp import load_dataset as load_mbjp_dataset
from src.datasets.progressive_obfuscation import load_dataset as load_progressive_obfuscation_dataset
from src.datasets.scalabrino import load_dataset as load_scalabrino_dataset
from src.datasets.schnappinger import load_dataset as load_schnappinger_dataset
from src.datasets.types import DatasetItem


def load_code_dataset(path: Path) -> list[DatasetItem]:
    if path.is_dir():
        if (
            (path / "manifest.jsonl").is_file()
            and (path / "provenance.json").is_file()
            and (path / "level-00-original").is_dir()
        ):
            return load_progressive_obfuscation_dataset(path)
        if (path / "scores").is_dir() and (path / "snippets").is_dir():
            return load_dorn_dataset(path)
        if (path / "dataset" / "scores").is_dir() and (path / "dataset" / "snippets").is_dir():
            return load_dorn_dataset(path)
        if (path / "scores.csv").is_file() and (path / "Snippets").is_dir():
            return load_scalabrino_dataset(path)
        if (path / "dataset" / "scores.csv").is_file() and (path / "dataset" / "Snippets").is_dir():
            return load_scalabrino_dataset(path)
        if (path / "labels.csv").exists():
            return load_schnappinger_dataset(path)
        if (path / "snippets_with_human_scores.csv").exists():
            return load_jetbrains_dataset(path)
        if (path / "raw" / "readability-votes.csv").is_file() and (path / "snippets").is_dir():
            return load_buse_dataset(path)
        raise ValueError(f"Unsupported code dataset directory: {path}")

    if path.suffix == ".jsonl":
        return load_code_jsonl_dataset(path)
    if path.name == "labels.csv":
        return load_schnappinger_dataset(path)
    if path.name in {"snippets.csv", "snippets_with_human_scores.csv"}:
        return load_jetbrains_dataset(path)
    if path.name == "readability-votes.csv":
        return load_buse_dataset(path)
    if path.suffix == ".json":
        return load_mbjp_dataset(path)
    raise ValueError(f"Unsupported code dataset path: {path}")
