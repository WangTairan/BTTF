import json
from pathlib import Path
from typing import Any

from src.datasets.types import DatasetItem


def load_dataset(path: Path) -> list[DatasetItem]:
    items = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            validate_row(row, line_number)
            content = str(row["code_snippet"] if "code_snippet" in row else row["code"])
            task_id = task_id_for_row(row)
            score = readability_score(row)
            metadata = metadata_for_row(row, path=path)
            metadata["raw_dataset"] = path.stem

            items.append(
                DatasetItem(
                    task_id=task_id,
                    content=content,
                    readability_score=score,
                    readability_prompt=row.get("readability"),
                    metadata=metadata,
                )
            )
    print(f"Loaded {len(items)} items from {path}", flush=True)
    return items


def validate_row(row: Any, line_number: int) -> None:
    if not isinstance(row, dict):
        raise ValueError(f"JSONL row {line_number} is not an object")
    old_schema = {"name", "code_snippet", "score"}.issubset(row)
    generated_schema = {"code", "readability"}.issubset(row) and (
        "item_id" in row or {"dataset", "source_id"}.issubset(row)
    )
    if not old_schema and not generated_schema:
        raise ValueError(
            f"JSONL row {line_number} must use either "
            "name/code_snippet/score, item_id/code/readability, "
            "or dataset/source_id/code/readability fields"
        )


def metadata_for_row(row: dict[str, Any], *, path: Path) -> dict[str, Any]:
    excluded = {"name", "code_snippet", "score", "item_id", "code"}
    metadata = {key: value for key, value in row.items() if key not in excluded}
    if "readability" in row:
        metadata["readability_label"] = row["readability"]
        metadata["readability_prompt"] = row["readability"]
        metadata["readability_ordinal"] = readability_score(row)
    metadata["jsonl_source"] = path.name
    return metadata


def task_id_for_row(row: dict[str, Any]) -> str:
    if "name" in row:
        return str(row["name"])
    if "item_id" in row:
        return str(row["item_id"])
    parts = [
        str(row["dataset"]),
        str(row["source_id"]),
        str(row["readability"]),
    ]
    if row.get("generator_model") is not None:
        parts.append(str(row["generator_model"]))
    return "__".join(parts)


def readability_score(row: dict[str, Any]) -> float | None:
    if "score" in row:
        return coerce_float(row.get("score"))
    label = row.get("readability")
    if label is None:
        return None
    mapping = {"low": 0.0, "normal": 0.5, "medium": 0.5, "high": 1.0}
    normalized = str(label).strip().lower()
    if normalized not in mapping:
        raise ValueError(f"Unsupported readability label: {label!r}")
    return mapping[normalized]


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
