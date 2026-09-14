from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from readability_data.java_degradation.engine import JavaInterferenceEngine
from readability_data.java_degradation.interferences.core.base import Interference
from readability_data.java_degradation.registry import interference_registry
from readability_data.shared.alignment import INTERFERENCE_SPEC_BY_SLUG
from readability_data.shared.explorer import write_degradation_report


@dataclass(frozen=True)
class SourceClass:
    identity: str
    path: Path
    relative_path: str
    content: bytes
    metadata: dict[str, object]


def construct_interference_dataset(
    input_root: Path,
    output: Path,
    seed: int,
    interferences: list[str] | None = None,
) -> dict[str, object]:
    """Apply each selected interference directly and separately to every source."""
    input_root = input_root.resolve()
    if not input_root.is_dir():
        raise ValueError(f"input Java directory not found: {input_root}")
    if output.exists():
        raise ValueError(f"output path already exists: {output}")
    registry = interference_registry()
    selected = list(registry) if interferences is None else list(interferences)
    if not selected:
        raise ValueError("at least one interference must be selected")
    if len(selected) != len(set(selected)):
        raise ValueError("each interference may be selected only once")
    unknown = set(selected) - registry.keys()
    if unknown:
        raise ValueError(f"unknown interferences: {sorted(unknown)}")

    sources, source_manifest = _load_sources(input_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    records: list[dict[str, object]] = []
    try:
        for base in sources:
            degrader = JavaInterferenceEngine(seed)
            original = _write_interference_variant(
                staging, base, base.content, 0, None, {}, None
            )
            records.append(original)
            for order, slug in enumerate(selected, start=1):
                plugin = registry[slug]
                result = degrader.apply_interferences(
                    base.content, base.identity, [slug]
                )
                prefix = f"{slug}_"
                stats = {
                    (key[len(prefix) :] if key.startswith(prefix) else key): value
                    for key, value in result.stats.items()
                }
                records.append(
                    _write_interference_variant(
                        staging,
                        base,
                        result.content,
                        order,
                        plugin,
                        stats,
                        str(original["variant_id"]),
                    )
                )

        source_counts = Counter(
            str(record["source"]) for record in records if record["order"] == 0
        )
        counts_by_interference = Counter(
            str(record["interference"])
            for record in records
            if record["interference"] is not None
        )
        provenance: dict[str, object] = {
            "module": "source-interference",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "granularity": "class",
            "application_mode": "independent-interference",
            "seed": seed,
            "input": {
                "root": os.path.relpath(input_root),
                "path_base": "invocation-working-directory",
                "policy": "all recursively discovered Java files; no sampling",
                "java_file_count": len(sources),
                "manifest": os.path.relpath(source_manifest)
                if source_manifest
                else None,
                "manifest_sha256": (
                    hashlib.sha256(source_manifest.read_bytes()).hexdigest()
                    if source_manifest
                    else None
                ),
            },
            "base_class_count": len(sources),
            "interference_count": len(selected),
            "variant_count_including_originals": len(records),
            "base_counts_by_source": dict(sorted(source_counts.items())),
            "counts_by_interference": dict(sorted(counts_by_interference.items())),
            "interferences": [
                {
                    "order": order,
                    "category": registry[slug].category,
                    "slug": slug,
                    "description": registry[slug].description,
                    "target_policy": INTERFERENCE_SPEC_BY_SLUG[slug].target_policy,
                    "template_count": INTERFERENCE_SPEC_BY_SLUG[slug].template_count,
                    "application": "original-source",
                    "implementation": (
                        f"{registry[slug].__class__.__module__}."
                        f"{registry[slug].__class__.__name__}"
                    ),
                }
                for order, slug in enumerate(selected, start=1)
            ],
            "validation": {
                "parser": "tree-sitter-java",
                "policy": (
                    "source and every independently generated interference must parse "
                    "without syntax errors"
                ),
                "semantic_scope": (
                    "transformations are source-local; project-level compilation and "
                    "strict semantic equivalence are not claimed"
                ),
            },
        }
        _write_metadata(staging, records, provenance)
        write_degradation_report(staging, records, "Java Interference Explorer")
        staging.replace(output)
        return provenance
    except Exception:
        shutil.rmtree(staging)
        raise


def _load_sources(input_root: Path) -> tuple[list[SourceClass], Path | None]:
    java_paths = sorted(path for path in input_root.rglob("*.java") if path.is_file())
    if not java_paths:
        raise ValueError(f"no Java files found under: {input_root}")
    manifest_path, metadata_by_path = _discover_manifest(input_root)
    sources = []
    seen_identities: set[str] = set()
    for path in java_paths:
        content = path.read_bytes()
        relative = path.relative_to(input_root).as_posix()
        metadata = metadata_by_path.get(path.resolve(), {})
        identity = str(
            metadata.get("base_sample_id")
            or metadata.get("sample_id")
            or _source_identity(relative, content)
        )
        if identity in seen_identities:
            identity = _source_identity(relative, content)
        seen_identities.add(identity)
        sources.append(SourceClass(identity, path, relative, content, metadata))
    return sources, manifest_path


def _discover_manifest(
    input_root: Path,
) -> tuple[Path | None, dict[Path, dict[str, object]]]:
    candidates = (input_root / "manifest.jsonl", input_root.parent / "manifest.jsonl")
    for manifest in candidates:
        if not manifest.is_file():
            continue
        records = [
            json.loads(line)
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        mapping: dict[Path, dict[str, object]] = {}
        for record in records:
            local_path = record.get("local_path")
            if not local_path:
                continue
            path = (manifest.parent / str(local_path)).resolve()
            if path.is_file():
                mapping[path] = record
        return manifest, mapping
    return None, {}


def _source_identity(relative_path: str, content: bytes) -> str:
    digest = hashlib.sha256(relative_path.encode() + b"\0" + content).hexdigest()[:16]
    return f"source-{digest}"


def _write_interference_variant(
    root: Path,
    base: SourceClass,
    content: bytes,
    order: int,
    interference: Interference | None,
    stats: dict[str, int],
    parent_variant_id: str | None,
) -> dict[str, object]:
    slug = "original" if interference is None else str(interference.slug)
    category = "source" if interference is None else str(interference.category)
    digest = hashlib.sha256(
        f"{base.identity}:independent-interference:{slug}".encode()
    ).hexdigest()[:12]
    label = "SRC" if order == 0 else f"I{order:02d}"
    variant_id = f"int-{digest}-{label}"
    unit_name = str(base.metadata.get("unit_name") or base.path.stem)
    source = str(base.metadata.get("source") or "source-directory")
    source_name = str(base.metadata.get("source_name") or source)
    directory = "source-original" if order == 0 else f"{category}/{slug}"
    filename = (
        "__".join(
            (
                label,
                _safe_component(source, 40),
                _safe_component(unit_name, 70),
                digest[-8:],
            )
        )
        + ".java"
    )
    destination = root / directory / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    original_hash = str(
        base.metadata.get("original_content_sha256")
        or base.metadata.get("content_sha256")
        or hashlib.sha256(base.content).hexdigest()
    )
    return {
        "variant_id": variant_id,
        "base_sample_id": base.identity,
        "parent_variant_id": parent_variant_id,
        "order": order,
        "level": order,
        "display_label": label,
        "stage": slug,
        "interference": None if interference is None else slug,
        "category": category,
        "description": (
            "Unmodified source class"
            if interference is None
            else str(interference.description)
        ),
        "application_mode": "independent-interference",
        "applied_interferences": [] if interference is None else [slug],
        "transformation_stats": stats,
        "construction_source": "pluggable-java-degrader",
        "readability_direction": "baseline" if order == 0 else "decreasing",
        "granularity": "class",
        "source": source,
        "source_name": source_name,
        "source_path": base.metadata.get("source_path", base.relative_path),
        "base_local_path": base.relative_path,
        "group_id": base.metadata.get("group_id", base.identity),
        "unit_kind": base.metadata.get("unit_kind", "class"),
        "unit_name": unit_name,
        "original_content_sha256": original_hash,
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "line_count": len(content.decode("utf-8").splitlines()),
        "local_path": destination.relative_to(root).as_posix(),
    }


def _write_metadata(
    root: Path,
    records: list[dict[str, object]],
    provenance: dict[str, object],
) -> None:
    (root / "manifest.jsonl").write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    (root / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_component(value: str, limit: int) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return (cleaned or "unknown")[:limit]
