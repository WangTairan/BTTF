"""Construct independent source-level Java interference datasets."""

from readability_data.java_degradation.engine import JavaInterferenceEngine
from readability_data.java_degradation.pipeline import (
    construct_interference_dataset,
)
from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG,
    interference_registry,
)

__all__ = [
    "JavaInterferenceEngine",
    "INTERFERENCE_CATALOG",
    "construct_interference_dataset",
    "interference_registry",
]
