from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.datasets.types import DatasetItem


MANIFEST_NAME = "manifest.jsonl"
MIN_LEVEL = 0
MAX_LEVEL = 6


def load_dataset(path: Path) -> list[DatasetItem]:
    dataset_dir = normalize_dataset_dir(path)
    manifest_path = dataset_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"Missing progressive-obfuscation manifest: {manifest_path}")

    items: list[DatasetItem] = []
    seen_variant_ids: set[str] = set()
    group_levels: dict[str, set[int]] = {}
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            validate_row(row, line_number)

            variant_id = str(row["variant_id"])
            if variant_id in seen_variant_ids:
                raise ValueError(f"Duplicate variant_id at manifest row {line_number}: {variant_id}")
            seen_variant_ids.add(variant_id)

            group_id = str(row["group_id"])
            level = int(row["level"])
            levels = group_levels.setdefault(group_id, set())
            if level in levels:
                raise ValueError(f"Duplicate level {level} for group {group_id!r}")
            levels.add(level)

            source_path = resolve_local_path(dataset_dir, str(row["local_path"]), line_number)
            content = source_path.read_text(encoding="utf-8")
            expected_sha256 = str(row["content_sha256"])
            actual_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if actual_sha256 != expected_sha256:
                raise ValueError(
                    f"Content hash mismatch at manifest row {line_number}: "
                    f"expected {expected_sha256}, got {actual_sha256}"
                )

            metadata = dict(row)
            metadata.update(
                {
                    "raw_dataset": "java_progressive_obfuscation",
                    "language": "java",
                    "manifest_row": line_number,
                    "readability_ordinal": readability_score(level),
                    "label_provenance": "cumulative_obfuscation_stage",
                }
            )
            items.append(
                DatasetItem(
                    task_id=variant_id,
                    content=content,
                    readability_score=readability_score(level),
                    readability_prompt=row.get("stage"),
                    metadata=metadata,
                )
            )

    expected_levels = set(range(MIN_LEVEL, MAX_LEVEL + 1))
    incomplete = {
        group_id: sorted(expected_levels - levels)
        for group_id, levels in group_levels.items()
        if levels != expected_levels
    }
    if incomplete:
        example_group, missing = next(iter(incomplete.items()))
        raise ValueError(
            f"Incomplete progressive group {example_group!r}: missing levels {missing}; "
            f"{len(incomplete)} incomplete groups in total"
        )

    items.sort(key=lambda item: (str(item.metadata["group_id"]), int(item.metadata["level"])))
    print(
        f"Loaded {len(items)} progressive-obfuscation variants "
        f"from {dataset_dir} ({len(group_levels)} groups)",
        flush=True,
    )
    return items


def normalize_dataset_dir(path: Path) -> Path:
    if path.is_file():
        if path.name != MANIFEST_NAME:
            raise ValueError(f"Unsupported progressive-obfuscation file: {path}")
        return path.parent
    return path


def validate_row(row: Any, line_number: int) -> None:
    required = {
        "variant_id",
        "group_id",
        "level",
        "stage",
        "local_path",
        "content_sha256",
        "source",
    }
    if not isinstance(row, dict):
        raise ValueError(f"Manifest row {line_number} is not an object")
    missing = sorted(required - set(row))
    if missing:
        raise ValueError(f"Manifest row {line_number} is missing fields: {missing}")
    level = int(row["level"])
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise ValueError(f"Manifest row {line_number} has unsupported level: {level}")


def resolve_local_path(dataset_dir: Path, local_path: str, line_number: int) -> Path:
    root = dataset_dir.resolve()
    candidate = (dataset_dir / local_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Manifest row {line_number} escapes the dataset directory: {local_path}")
    if not candidate.is_file():
        raise ValueError(f"Missing source file at manifest row {line_number}: {candidate}")
    return candidate


def readability_score(level: int) -> float:
    """Map L0..L6 to a higher-is-more-readable ordinal target in [0, 1]."""
    return 1.0 - (float(level) / MAX_LEVEL)
