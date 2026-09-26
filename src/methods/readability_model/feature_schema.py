"""Stable naming rules shared by readability feature tables and models."""

from __future__ import annotations


FEATURE_FAMILIES = ("base", "embedding", "llm")


def feature_family(name: str) -> str:
    """Map a public column to its storage family without changing frozen names."""
    prefix, separator, _ = name.partition("__")
    if not separator:
        raise ValueError(f"Expected a namespaced feature, received {name!r}.")
    if prefix in {"base", "compression"}:
        return "base"
    if prefix in {"embedding", "semantic"}:
        return "embedding"
    if prefix == "llm":
        return "llm"
    raise ValueError(f"Unknown feature namespace: {prefix!r}.")


def namespaced_feature(prefix: str, column: str) -> str:
    """Return the public ML feature name for a raw table column."""
    if column.startswith(f"{prefix}__"):
        return column
    if prefix == "base" and column.startswith("compression_"):
        return f"compression__{column.removeprefix('compression_')}"
    if prefix == "embedding" and column.startswith("short_identifier_"):
        return f"semantic__{column}"
    return f"{prefix}__{column}"
