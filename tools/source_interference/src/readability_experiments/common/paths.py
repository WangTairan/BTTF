"""Default monorepo paths; explicit CLI paths remain supported."""

from __future__ import annotations

import os
from pathlib import Path


def repository_root() -> Path:
    override = os.environ.get("READABILITY_REPOSITORY_ROOT")
    candidates = (
        (Path(override).resolve(),) if override else Path(__file__).resolve().parents
    )
    for root in candidates:
        if (root / "datasets").is_dir() and (
            root / "tools/source_interference/pyproject.toml"
        ).is_file():
            return root
    raise RuntimeError(
        "Cannot locate the research repository. Use an editable installation or "
        "set READABILITY_REPOSITORY_ROOT to the repository root."
    )


def default_workspace() -> Path:
    return repository_root() / "artifacts/source_interference"


def constructed_dataset(language: str) -> Path:
    names = {
        "java": "java-comparative-obfuscation-class-100",
        "python": "python-comparative-degradation-class-100",
    }
    return repository_root() / "datasets/constructed" / names[language]


def default_results(provider: str) -> Path:
    return repository_root() / "results/experiments/source_interference" / provider
