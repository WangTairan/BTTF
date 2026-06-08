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
            content = str(row["code_snippet"])
            metadata = {
                key: value
                for key, value in row.items()
                if key not in {"name", "code_snippet", "score"}
            }
            metadata["raw_dataset"] = path.stem

            items.append(
                DatasetItem(
                    task_id=str(row["name"]),
                    content=content,
                    readability_score=coerce_float(row.get("score")),
                    metadata=metadata,
                )
            )
    print(f"Loaded {len(items)} items from {path}", flush=True)
    return items


def validate_row(row: Any, line_number: int) -> None:
    if not isinstance(row, dict):
        raise ValueError(f"JSONL row {line_number} is not an object")
    missing = [
        field
        for field in ("name", "code_snippet", "score")
        if field not in row
    ]
    if missing:
        raise ValueError(
            f"JSONL row {line_number} is missing fields: {', '.join(missing)}"
        )


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
