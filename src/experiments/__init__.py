"""Central experiment registry for datasets, methods, and output policies."""

from .registry import (
    COGNASCORE_DEFAULT_CACHE_DIR,
    COGNASCORE_DEFAULT_MODEL,
    DATASETS,
    METHODS,
    OUTPUT_POLICY_CONFIGURED_HISTORY,
    OUTPUT_POLICY_OVERWRITE,
    DatasetSpec,
    MethodSpec,
    method_choices,
    dataset_key_for_path,
    dataset_spec_for_path,
    is_method_dataset_supported,
    method_history_policy,
    method_output_key,
)

__all__ = [
    "COGNASCORE_DEFAULT_CACHE_DIR",
    "COGNASCORE_DEFAULT_MODEL",
    "DATASETS",
    "METHODS",
    "OUTPUT_POLICY_CONFIGURED_HISTORY",
    "OUTPUT_POLICY_OVERWRITE",
    "DatasetSpec",
    "MethodSpec",
    "method_choices",
    "dataset_key_for_path",
    "dataset_spec_for_path",
    "is_method_dataset_supported",
    "method_history_policy",
    "method_output_key",
]
