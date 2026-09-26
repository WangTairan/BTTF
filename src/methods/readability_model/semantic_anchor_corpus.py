"""Versioned, hash-verified semantic anchors used by the readability model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CORPUS_ROOT = Path(__file__).with_name("resources") / "semantic_anchor_corpus"
MANIFEST_PATH = CORPUS_ROOT / "manifest.json"
EXPECTED_ALGORITHM_VERSION = 1


def load_semantic_anchor_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("algorithm_version") != EXPECTED_ALGORITHM_VERSION:
        raise ValueError("Semantic-anchor algorithm version mismatch")
    for row in manifest["samples"]:
        path = CORPUS_ROOT / row["snippet_path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != row["text_sha256"]:
            raise ValueError(f"Semantic-anchor hash mismatch for {row['sample_id']}: {actual}")
    return manifest


def semantic_anchor_texts_by_category() -> dict[str, tuple[tuple[str, str], ...]]:
    manifest = load_semantic_anchor_manifest()
    grouped: dict[str, list[tuple[str, str]]] = {"mathematical": [], "application": []}
    for row in manifest["samples"]:
        category = str(row["category"])
        grouped[category].append(
            (
                str(row["sample_id"]),
                (CORPUS_ROOT / row["snippet_path"]).read_text(encoding="utf-8"),
            )
        )
    return {category: tuple(values) for category, values in grouped.items()}
