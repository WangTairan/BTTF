from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path("output")


def safe_path_part(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return safe or "unnamed"


def dataset_name_for_path(path: Path) -> str:
    from src.experiments.registry import dataset_key_for_path

    dataset_key = dataset_key_for_path(path)
    if dataset_key is not None:
        return dataset_key
    if path.parent.name == "datasets":
        return path.stem
    return path.parent.name


def output_dir(
    output_root: Path | None,
    method: str,
    dataset_name: str,
    *parts: str | None,
) -> Path:
    path = (output_root or DEFAULT_OUTPUT_ROOT) / safe_path_part(method) / safe_path_part(dataset_name)
    for part in parts:
        if part is not None:
            path /= safe_path_part(part)
    return path
