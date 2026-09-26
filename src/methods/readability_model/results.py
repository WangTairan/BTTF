from __future__ import annotations

import re


def model_slug(model_name: str) -> str:
    return slugify(model_name)


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "default"
