from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Corpus:
    language: str
    dataset_root: Path
    raw_roots: dict[str, Path]

    @property
    def manifest_path(self) -> Path:
        return self.dataset_root / "manifest.jsonl"

    def records(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def grouped_records(self) -> dict[str, list[dict[str, object]]]:
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for record in self.records():
            grouped[str(record["base_sample_id"])].append(record)
        for records in grouped.values():
            records.sort(key=lambda row: int(row["order"]))
        return dict(grouped)


def relative_path(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def dataset_fingerprint(root: Path) -> str:
    """Hash paths and bytes without changing the source dataset."""
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()
