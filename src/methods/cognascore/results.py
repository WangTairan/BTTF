from __future__ import annotations

from pathlib import Path
import re


def result_dir(root: Path, dataset: str, model_name: str, eps: float, min_pts: int) -> Path:
    return root / slugify(dataset) / model_slug(model_name)


def parameter_slug(model_name: str, eps: float, min_pts: int) -> str:
    return f"{model_slug(model_name)}__{dbscan_slug(eps, min_pts)}"


def model_slug(model_name: str) -> str:
    return slugify(model_name)


def dbscan_slug(eps: float, min_pts: int) -> str:
    return f"eps-{format_float(eps)}__minpts-{min_pts}"


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "default"


def format_float(value: float) -> str:
    return f"{value:g}"
