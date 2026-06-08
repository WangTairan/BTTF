from pathlib import Path
from typing import Any

from src.datasets.types import DatasetItem


def load_dataset(
    path: Path,
    id_column: str = "ID",
    text_column: str = "Excerpt",
    score_column: str = "BT_easiness",
) -> list[DatasetItem]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "CLEAR adapter requires pandas and openpyxl. Install requirements first."
        ) from exc

    frame = pd.read_excel(path)
    required = (id_column, text_column, score_column)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"CLEAR dataset is missing columns: {', '.join(missing)}")

    items = []
    for _, row in frame.iterrows():
        text = row[text_column]
        score = row[score_column]
        if pd.isna(text) or pd.isna(score):
            continue

        items.append(
            DatasetItem(
                task_id=f"CLEAR/{clean_scalar(row[id_column])}",
                content=str(text),
                readability_score=float(score),
                readability_prompt=clean_scalar(row.get("Lexile Band")),
                metadata={
                    "title": clean_scalar(row.get("Title")),
                    "author": clean_scalar(row.get("Author")),
                    "dev_bucket": clean_scalar(row.get("dev_bucket")),
                    "sentence_count": clean_scalar(row.get("sentence_count")),
                },
            )
        )
    return items


def clean_scalar(value: Any) -> Any:
    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except (ImportError, TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        value = value.item()
    return value

