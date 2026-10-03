import csv
import hashlib
from collections import Counter
from pathlib import Path, PureWindowsPath

from src.datasets.types import DatasetItem


DEFAULT_DATASET = Path("datasets/schnappinger")
LABEL_FIELDS = ("readability", "understandability", "complexity", "modularization", "overall")


def load_dataset(path: Path = DEFAULT_DATASET) -> list[DatasetItem]:
    root, labels_path = resolve_paths(path)
    items = []
    with labels_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        base_task_ids = [
            f"Schnappinger/{row['projectname']}/{row['packageandclass']}"
            for row in rows
        ]
        duplicate_task_ids = {
            task_id for task_id, count in Counter(base_task_ids).items() if count > 1
        }
        for line_number, (row, base_task_id) in enumerate(
            zip(rows, base_task_ids),
            start=2,
        ):
            source_parts = PureWindowsPath(row["path"]).parts
            source_path = root.joinpath(*source_parts)
            # The original CSV spells the project "jsweet", but the archive
            # directory is "Jsweet". Preserve both originals on case-sensitive
            # filesystems as well as macOS.
            if not source_path.exists() and source_parts[0] == "jsweet":
                source_path = root.joinpath("Jsweet", *source_parts[1:])
            if not source_path.exists():
                raise FileNotFoundError(
                    f"Schnappinger source on CSV line {line_number} does not exist: {source_path}"
                )
            probabilities = {
                field: parse_probability_vector(row[field], field, line_number)
                for field in LABEL_FIELDS
            }
            project = row["projectname"]
            qualified_class = row["packageandclass"]
            task_id = base_task_id
            if base_task_id in duplicate_task_ids:
                path_digest = hashlib.sha256(row["path"].encode("utf-8")).hexdigest()[:12]
                task_id = f"{base_task_id}#{path_digest}"
            items.append(
                DatasetItem(
                    task_id=task_id,
                    content=source_path.read_text(encoding="utf-8", errors="replace"),
                    readability_score=expected_readability(probabilities["readability"]),
                    metadata={
                        "project": project,
                        "class": qualified_class,
                        "source_path": str(source_path.relative_to(root)),
                        "label_probabilities": probabilities,
                        "readability_scale": "expected Likert score; 4=easy to read, 1=hard to read",
                    },
                )
            )
    return items


def resolve_paths(path: Path) -> tuple[Path, Path]:
    if path.is_dir():
        return path, path / "labels.csv"
    if path.name == "labels.csv":
        return path.parent, path
    raise ValueError("Schnappinger path must be its dataset directory or labels.csv")


def parse_probability_vector(value: str, field: str, line_number: int) -> list[float]:
    text = value.strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError(f"Invalid {field} probabilities on CSV line {line_number}: {value}")
    probabilities = [float(part) for part in text[1:-1].split(",")]
    if len(probabilities) != 4:
        raise ValueError(f"Expected four {field} probabilities on CSV line {line_number}")
    return probabilities


def expected_readability(probabilities: list[float]) -> float:
    return sum(probability * score for probability, score in zip(probabilities, (4, 3, 2, 1)))
