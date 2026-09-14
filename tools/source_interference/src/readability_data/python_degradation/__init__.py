"""Independent source-level readability degradation for Python classes."""

from .pipeline import construct_python_dataset
from .registry import INTERFERENCES

__all__ = ["INTERFERENCES", "construct_python_dataset"]
