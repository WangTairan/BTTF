from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from src.datasets.types import DatasetItem


SNIPPET_COUNT = 100


def load_dataset(path: Path) -> list[DatasetItem]:
    dataset_dir = normalize_dataset_dir(path)
    snippets_dir = dataset_dir / "snippets"
    votes_path = dataset_dir / "raw" / "readability-votes.csv"
    if not snippets_dir.is_dir() or not votes_path.is_file():
        raise ValueError(f"Unsupported Buse dataset directory: {path}")

    rows = list(csv.reader(votes_path.open("r", encoding="utf-8")))
    if not rows:
        raise ValueError(f"Empty Buse vote file: {votes_path}")
    for line_number, row in enumerate(rows, start=1):
        if len(row) != SNIPPET_COUNT + 2:
            raise ValueError(
                f"Buse vote row {line_number} has {len(row)} columns; "
                f"expected {SNIPPET_COUNT + 2}"
            )

    courses = Counter(row[1].strip() for row in rows)
    ratings_by_snippet: dict[int, list[float]] = {index: [] for index in range(1, SNIPPET_COUNT + 1)}
    for row in rows:
        for snippet_id, value in enumerate(row[2:], start=1):
            value = value.strip()
            if value:
                ratings_by_snippet[snippet_id].append(float(value))

    items: list[DatasetItem] = []
    for snippet_id in range(1, SNIPPET_COUNT + 1):
        source_path = snippets_dir / f"{snippet_id}.jsnp"
        if not source_path.is_file():
            raise ValueError(f"Missing Buse snippet: {source_path}")
        ratings = ratings_by_snippet[snippet_id]
        if not ratings:
            raise ValueError(f"Buse snippet {snippet_id} has no ratings")
        items.append(
            DatasetItem(
                task_id=f"Buse/{snippet_id}",
                content=source_path.read_text(encoding="utf-8"),
                readability_score=sum(ratings) / len(ratings),
                metadata={
                    "raw_dataset": "buse",
                    "language": "java",
                    "source_id": snippet_id,
                    "rating_count": len(ratings),
                    "rating_min": min(ratings),
                    "rating_max": max(ratings),
                    "course_counts": dict(sorted(courses.items())),
                },
            )
        )

    print(f"Loaded {len(items)} Buse items from {dataset_dir}", flush=True)
    return items


def normalize_dataset_dir(path: Path) -> Path:
    if path.is_file():
        if path.name == "readability-votes.csv" and path.parent.name == "raw":
            return path.parent.parent
        return path.parent
    return path
