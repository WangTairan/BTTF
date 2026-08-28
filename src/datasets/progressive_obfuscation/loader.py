"""Backward-compatible import for the original progressive dataset adapter."""

from src.datasets.constructed_variants.loader import load_dataset

__all__ = ["load_dataset"]
