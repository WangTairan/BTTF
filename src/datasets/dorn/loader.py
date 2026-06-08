import csv
from pathlib import Path

from src.datasets.types import DatasetItem


DORN_LANGUAGES = ("cuda", "java", "python")


def load_dataset(path: Path) -> list[DatasetItem]:
    dataset_dir = normalize_dataset_dir(path)
    scores_dir = dataset_dir / "scores"
    snippets_dir = dataset_dir / "snippets"
    if not scores_dir.is_dir() or not snippets_dir.is_dir():
        raise ValueError(f"Unsupported Dorn dataset directory: {path}")

    items: list[DatasetItem] = []
    for language in DORN_LANGUAGES:
        items.extend(load_language(scores_dir, snippets_dir, language))

    print(f"Loaded {len(items)} Dorn items from {dataset_dir}", flush=True)
    return items


def normalize_dataset_dir(path: Path) -> Path:
    if (path / "dataset").is_dir():
        return path / "dataset"
    return path


def load_language(scores_dir: Path, snippets_dir: Path, language: str) -> list[DatasetItem]:
    language_snippets_dir = snippets_dir / language
    score_path = scores_dir / f"{language}.csv"
    if not language_snippets_dir.is_dir() or not score_path.is_file():
        return []

    snippet_ids = sorted(int(path.stem) for path in language_snippets_dir.glob("*.jsnp"))
    score_rows = list(csv.reader(score_path.open("r", encoding="utf-8")))
    items: list[DatasetItem] = []
    for column_index, snippet_id in enumerate(snippet_ids, start=1):
        ratings = column_ratings(score_rows, column_index)
        score = sum(ratings) / len(ratings) if ratings else None
        source_path = language_snippets_dir / f"{snippet_id}.jsnp"
        items.append(
            DatasetItem(
                task_id=f"Dorn/{language}/{snippet_id}",
                content=source_path.read_text(encoding="utf-8"),
                readability_score=score,
                metadata={
                    "raw_dataset": "dorn",
                    "language": language,
                    "source_id": snippet_id,
                    "rating_count": len(ratings),
                },
            )
        )
    return items


def column_ratings(rows: list[list[str]], column_index: int) -> list[float]:
    ratings: list[float] = []
    for row in rows:
        if column_index >= len(row):
            continue
        value = row[column_index].strip()
        if value:
            ratings.append(float(value))
    return ratings
