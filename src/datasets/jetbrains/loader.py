import csv
from pathlib import Path

from src.datasets.types import DatasetItem


DEFAULT_DATASET = Path("datasets/jetbrains")


def load_dataset(path: Path = DEFAULT_DATASET) -> list[DatasetItem]:
    root = path if path.is_dir() else path.parent
    snippets = read_snippets(root / "snippets.csv")
    scores_path = root / "snippets_with_human_scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"JetBrains human score file does not exist: {scores_path}")

    items = []
    with scores_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            snippet_id = row["snip_id"]
            snippet = snippets.get(snippet_id)
            if snippet is None:
                raise ValueError(
                    f"JetBrains score on CSV line {line_number} has no snippet: {snippet_id}"
                )
            readable = float(row["readable"])
            unreadable = float(row["unreadable"])
            vote_total = readable + unreadable
            human_vote_fraction = readable / vote_total if vote_total else None
            binary_readability = int(row["readability"])
            items.append(
                DatasetItem(
                    task_id=f"JetBrains/{snippet_id}",
                    content=snippet["snippet"],
                    readability_score=float(binary_readability),
                    readability_prompt=snippet["task"],
                    metadata={
                        "snippet_id": snippet_id,
                        "readable_votes": readable,
                        "unreadable_votes": unreadable,
                        "human_readable_vote_fraction": human_vote_fraction,
                        "neutral": row["neutral"].lower() == "true",
                        "binary_readability": binary_readability,
                        "evaluation_metric": "mcc",
                        "existing_metrics": {
                            "posnett": int(row["posnett"]),
                            "dorn_reversed": int(row["dorn_reversed"]),
                            "scalabrino_reversed": int(row["scalabrino_reverced"]),
                            "mi": int(row["mi"]),
                        },
                        "readability_scale": "binary human readability classification; 1=readable, 0=unreadable",
                    },
                )
            )
    return items


def read_snippets(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"JetBrains snippet file does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["snip_id"]: row for row in csv.DictReader(handle)}
