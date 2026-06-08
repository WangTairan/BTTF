import csv
from pathlib import Path, PureWindowsPath

from src.datasets.types import DatasetItem


DEFAULT_DATASET = Path("datasets/schnappinger")
LABEL_FIELDS = ("readability", "understandability", "complexity", "modularization", "overall")


def load_dataset(path: Path = DEFAULT_DATASET) -> list[DatasetItem]:
    root, labels_path = resolve_paths(path)
    items = []
    with labels_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            source_path = root.joinpath(*PureWindowsPath(row["path"]).parts)
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
            items.append(
                DatasetItem(
                    task_id=f"Schnappinger/{project}/{qualified_class}",
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
