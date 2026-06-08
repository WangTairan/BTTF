import json
from pathlib import Path
from typing import Any

from src.datasets.types import DatasetItem


def load_dataset(path: Path) -> list[DatasetItem]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("MBJP dataset must be a JSON list")

    items = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Dataset item {index} is not an object")
        if "task_id" not in item or "code" not in item:
            raise ValueError(f"Dataset item {index} must contain task_id and code")

        items.append(
            DatasetItem(
                task_id=str(item["task_id"]),
                content=normalize_escaped_newlines(str(item["code"])),
                readability_score=coerce_float(item.get("readability_score")),
                readability_prompt=item.get("readability_prompt"),
            )
        )
    return items


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def normalize_escaped_newlines(text: str) -> str:
    return text.replace("\\r\\n", "\n").replace("\\n", "\n").replace('\\"', '"')
