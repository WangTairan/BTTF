"""Stable naming rules shared by readability feature tables and models."""

from __future__ import annotations


FEATURE_FAMILIES = ("base", "embedding", "llm")

# Historical tables remain readable through these one-way aliases. New tables,
# configurations, and model metadata use the canonical names on the right.
LEGACY_FEATURE_ALIASES = {
    "base__expression_complexity": "base__expression_literal_density",
    "embedding__structural_core__auto_kmeans_pattern_count": (
        "embedding__computation_control_pattern_count"
    ),
    "llm__literal_tail_difficulty": "llm__literal_tail_surprisal",
    "llm__identifier_onset_difficulty": "llm__identifier_onset_surprisal",
    "llm__assignment_value_difficulty": "llm__assignment_value_surprisal",
    "llm__declaration_difficulty_variation": (
        "llm__declaration_surprisal_variation"
    ),
}


FINAL_FEATURE_DISPLAY_NAMES = {
    "base__operator_density": "Operator density",
    "llm__literal_tail_surprisal": "Literal-tail surprisal",
    "llm__identifier_onset_surprisal": "Identifier-onset surprisal",
    "embedding__computation_control_pattern_count": (
        "Computation-and-control pattern count"
    ),
    "base__decision_density": "Decision density",
    "base__expression_literal_density": "Expression-literal density",
    "base__longest_line_length": "Longest line length",
    "llm__assignment_value_surprisal": "Assignment-value surprisal",
    "llm__declaration_surprisal_variation": "Declaration-surprisal variation",
    "llm__short_identifier_context_dependence": (
        "Short-identifier context dependence"
    ),
    "embedding__only_identifier__embedding_dispersion": (
        "Identifier embedding dispersion"
    ),
}


def canonical_feature_name(name: str) -> str:
    """Return the current public key for a historical or current feature name."""
    return LEGACY_FEATURE_ALIASES.get(name, name)


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
        return canonical_feature_name(column)
    if prefix == "base" and column.startswith("compression_"):
        name = f"compression__{column.removeprefix('compression_')}"
        return canonical_feature_name(name)
    if prefix == "embedding" and column.startswith("short_identifier_"):
        return canonical_feature_name(f"semantic__{column}")
    return canonical_feature_name(f"{prefix}__{column}")


def feature_display_name(name: str) -> str:
    """Return the paper-facing name of a retained feature when one is defined."""
    canonical = canonical_feature_name(name)
    return FINAL_FEATURE_DISPLAY_NAMES.get(canonical, canonical)
