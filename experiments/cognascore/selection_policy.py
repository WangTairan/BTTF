"""Theory-driven exclusions shared by CognaScore feature-selection experiments.

The features remain in the produced tables for diagnostics and ablations, but
formal model-selection scripts must not select them by default.
"""

from __future__ import annotations


EXCLUDED_CLUSTER_SIZE_FEATURES = (
    "embedding__only_identifier__optics_cluster_size_cv",
    "embedding__structural_core__optics_cluster_size_cv",
    "embedding__semantic_core__auto_kmeans_cluster_size_cv",
)

EXCLUDED_ABSOLUTE_VERTICAL_FEATURES = (
    "base__visual_identifier_y_mean",
    "base__visual_identifier_y_std",
    "base__visual_keyword_y_mean",
    "base__visual_keyword_y_std",
    "base__visual_operator_y_mean",
    "base__visual_operator_y_std",
    "base__visual_period_y_mean",
    "base__scalabrino_visual_comment_y_mean",
    "base__scalabrino_visual_number_y_mean",
    "base__chunk_y_mean",
)

EXCLUDED_PUNCTUATION_DIAGNOSTICS = (
    "base__visual_period_density",
    "base__visual_period_y_std",
    "base__scalabrino_visual_comma_dft_energy",
)

DEFAULT_EXCLUDED_FEATURES = (
    *EXCLUDED_CLUSTER_SIZE_FEATURES,
    *EXCLUDED_ABSOLUTE_VERTICAL_FEATURES,
    *EXCLUDED_PUNCTUATION_DIAGNOSTICS,
)


def with_default_exclusions(extra: list[str] | tuple[str, ...]) -> list[str]:
    """Return stable, de-duplicated default and command-line exclusions."""
    return list(dict.fromkeys((*DEFAULT_EXCLUDED_FEATURES, *extra)))
