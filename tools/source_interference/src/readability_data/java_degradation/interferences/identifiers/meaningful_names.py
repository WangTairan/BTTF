"""Backward-compatible imports for shared meaningful-name resources."""

from readability_data.shared.meaningful_names import (
    LOCAL_MEANINGFUL_NAMES,
    METHOD_MEANINGFUL_NAMES,
    choose_misleading_name,
    ranked_meaningful_names,
    ranked_misleading_names,
)

__all__ = [
    "LOCAL_MEANINGFUL_NAMES",
    "METHOD_MEANINGFUL_NAMES",
    "choose_misleading_name",
    "ranked_misleading_names",
    "ranked_meaningful_names",
]
