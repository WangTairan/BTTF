"""Stable naming rules shared by CognaScore feature tables and models."""

from __future__ import annotations


def namespaced_feature(prefix: str, column: str) -> str:
    """Return the public ML feature name for a raw table column."""
    if column.startswith(f"{prefix}__"):
        return column
    if prefix == "base" and column.startswith("compression_"):
        return f"compression__{column.removeprefix('compression_')}"
    if prefix == "embedding" and column.startswith("short_identifier_"):
        return f"semantic__{column}"
    return f"{prefix}__{column}"
