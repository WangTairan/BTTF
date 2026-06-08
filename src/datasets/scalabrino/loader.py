import csv
from pathlib import Path

from src.datasets.types import DatasetItem


def load_dataset(path: Path) -> list[DatasetItem]:
    dataset_dir = normalize_dataset_dir(path)
    snippets_dir = dataset_dir / "Snippets"
    score_path = dataset_dir / "scores.csv"
    if not snippets_dir.is_dir() or not score_path.is_file():
        raise ValueError(f"Unsupported Scalabrino dataset directory: {path}")

    score_rows = list(csv.reader(score_path.open("r", encoding="utf-8")))
    if not score_rows:
        raise ValueError(f"Empty Scalabrino score file: {score_path}")

    snippet_ids = parse_header(score_rows[0])
    items: list[DatasetItem] = []
    for column_index, snippet_id in enumerate(snippet_ids, start=1):
        ratings = column_ratings(score_rows[1:], column_index)
        score = sum(ratings) / len(ratings) if ratings else None
        source_path = snippets_dir / f"{snippet_id}.jsnp"
        items.append(
            DatasetItem(
                task_id=f"Scalabrio{snippet_id}",
                content=source_path.read_text(encoding="utf-8"),
                readability_score=score,
                metadata={
                    "raw_dataset": "scalabrino",
                    "language": "java",
                    "source_id": snippet_id,
                    "rating_count": len(ratings),
                },
            )
        )

    print(f"Loaded {len(items)} Scalabrino items from {dataset_dir}", flush=True)
    return items


def normalize_dataset_dir(path: Path) -> Path:
    if (path / "dataset").is_dir():
        return path / "dataset"
    return path


def parse_header(header: list[str]) -> list[int]:
    snippet_ids: list[int] = []
    for value in header[1:]:
        value = value.strip()
        if not value.startswith("Snippet"):
            raise ValueError(f"Unexpected Scalabrino score column: {value!r}")
        snippet_ids.append(int(value.removeprefix("Snippet")))
    return snippet_ids


def column_ratings(rows: list[list[str]], column_index: int) -> list[float]:
    ratings: list[float] = []
    for row in rows:
        if column_index >= len(row):
            continue
        value = row[column_index].strip()
        if value:
            ratings.append(float(value))
    return ratings
