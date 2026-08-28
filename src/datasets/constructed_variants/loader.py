from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.datasets.types import DatasetItem


MANIFEST_NAME = "manifest.jsonl"
PROVENANCE_NAME = "provenance.json"

DATASET_KEYS_BY_MODULE = {
    "source-degradation": "java_progressive_obfuscation",
    "source-interference": "java_comparative_obfuscation",
}


def load_dataset(path: Path) -> list[DatasetItem]:
    dataset_dir = normalize_dataset_dir(path)
    provenance = load_provenance(dataset_dir)
    dataset_key = dataset_key_from_provenance(provenance)
    application_mode = str(provenance.get("application_mode") or "cumulative")
    manifest_path = dataset_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"Missing constructed-variant manifest: {manifest_path}")

    items: list[DatasetItem] = []
    seen_variant_ids: set[str] = set()
    group_positions: dict[str, set[int]] = {}
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
            position = row_position(row)
            positions = group_positions.setdefault(group_id, set())
            if position in positions:
                raise ValueError(
                    f"Duplicate position {position} for constructed group {group_id!r}"
                )
            positions.add(position)

            source_path = resolve_local_path(dataset_dir, str(row["local_path"]), line_number)
            content = source_path.read_text(encoding="utf-8")
            verify_content_hash(content, row, line_number)

            score, label_provenance = label_for_row(
                row,
                application_mode=application_mode,
                provenance=provenance,
            )
            metadata = dict(row)
            metadata.update(
                {
                    "raw_dataset": dataset_key,
                    "language": "java",
                    "manifest_row": line_number,
                    "constructed_application_mode": application_mode,
                    "is_baseline_variant": position == 0,
                    "label_provenance": label_provenance,
                }
            )
            items.append(
                DatasetItem(
                    task_id=variant_id,
                    content=content,
                    readability_score=score,
                    readability_prompt=row.get("display_label") or row.get("stage"),
                    metadata=metadata,
                )
            )

    expected_positions = expected_group_positions(provenance)
    validate_complete_groups(group_positions, expected_positions)
    expected_count = provenance.get("variant_count_including_originals")
    if expected_count is not None and len(items) != int(expected_count):
        raise ValueError(
            f"Constructed manifest contains {len(items)} rows; provenance declares "
            f"{int(expected_count)}"
        )

    items.sort(
        key=lambda item: (
            str(item.metadata["group_id"]),
            row_position(item.metadata),
        )
    )
    print(
        f"Loaded {len(items)} {dataset_key} variants from {dataset_dir} "
        f"({len(group_positions)} groups; mode={application_mode})",
        flush=True,
    )
    return items


def normalize_dataset_dir(path: Path) -> Path:
    if path.is_file():
        if path.name not in {MANIFEST_NAME, PROVENANCE_NAME}:
            raise ValueError(f"Unsupported constructed-variant file: {path}")
        return path.parent
    return path


def load_provenance(dataset_dir: Path) -> dict[str, Any]:
    path = dataset_dir / PROVENANCE_NAME
    if not path.is_file():
        raise ValueError(f"Missing constructed-variant provenance: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Constructed-variant provenance is not an object: {path}")
    return payload


def dataset_key_from_provenance(provenance: dict[str, Any]) -> str:
    module = str(provenance.get("module") or "")
    try:
        return DATASET_KEYS_BY_MODULE[module]
    except KeyError as exc:
        raise ValueError(f"Unsupported constructed dataset module: {module!r}") from exc


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
    if int(row["level"]) < 0:
        raise ValueError(f"Manifest row {line_number} has a negative level")


def row_position(row: dict[str, Any]) -> int:
    return int(row.get("order", row["level"]))


def expected_group_positions(provenance: dict[str, Any]) -> set[int]:
    if "counts_by_level" in provenance:
        return {int(level) for level in provenance["counts_by_level"]}
    if "interference_count" in provenance:
        return set(range(int(provenance["interference_count"]) + 1))
    raise ValueError("Constructed provenance does not declare levels or interferences")


def validate_complete_groups(
    group_positions: dict[str, set[int]],
    expected_positions: set[int],
) -> None:
    incomplete = {
        group_id: {
            "missing": sorted(expected_positions - positions),
            "unexpected": sorted(positions - expected_positions),
        }
        for group_id, positions in group_positions.items()
        if positions != expected_positions
    }
    if incomplete:
        example_group, differences = next(iter(incomplete.items()))
        raise ValueError(
            f"Incomplete constructed group {example_group!r}: {differences}; "
            f"{len(incomplete)} incomplete groups in total"
        )


def resolve_local_path(dataset_dir: Path, local_path: str, line_number: int) -> Path:
    root = dataset_dir.resolve()
    candidate = (dataset_dir / local_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Manifest row {line_number} escapes the dataset directory: {local_path}")
    if not candidate.is_file():
        raise ValueError(f"Missing source file at manifest row {line_number}: {candidate}")
    return candidate


def verify_content_hash(content: str, row: dict[str, Any], line_number: int) -> None:
    expected = str(row["content_sha256"])
    actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if actual != expected:
        raise ValueError(
            f"Content hash mismatch at manifest row {line_number}: "
            f"expected {expected}, got {actual}"
        )


def label_for_row(
    row: dict[str, Any],
    *,
    application_mode: str,
    provenance: dict[str, Any],
) -> tuple[float | None, str]:
    if application_mode == "cumulative":
        positions = expected_group_positions(provenance)
        maximum = max(positions)
        if maximum <= 0:
            raise ValueError("Cumulative constructed dataset needs at least one degraded level")
        return 1.0 - float(row_position(row)) / float(maximum), "cumulative_obfuscation_stage"

    if application_mode in {"independent", "independent-interference"}:
        # Independent transformations have no justified total severity order.  Their
        # expected direction is retained in metadata for paired evaluation instead.
        return None, "paired_expected_readability_direction"

    raise ValueError(f"Unsupported constructed application mode: {application_mode!r}")
