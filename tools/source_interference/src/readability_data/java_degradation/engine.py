from __future__ import annotations

from collections.abc import Iterable

from readability_data.java_degradation.interferences.core.base import (
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import validate_java
from readability_data.java_degradation.registry import interference_registry


class JavaInterferenceEngine:
    """Apply explicit source interferences to a complete Java class."""

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def apply_interferences(
        self,
        source: bytes,
        identity: str,
        slugs: Iterable[str],
    ) -> TransformResult:
        """Apply an explicit ordered plugin sequence outside the L1-L6 profile."""
        requested = tuple(slugs)
        if len(requested) != len(set(requested)):
            raise ValueError("an interference may be selected only once per sequence")
        registry = interference_registry()
        unknown = set(requested) - registry.keys()
        if unknown:
            raise ValueError(f"unknown interferences: {sorted(unknown)}")

        validate_java(source, identity, "source")
        context = InterferenceContext(self.seed, identity)
        current = source
        stats: dict[str, int] = {}
        for slug in requested:
            result = registry[slug].apply(current, context)
            validate_java(result.content, identity, slug)
            current = result.content
            stats.update(
                {f"{slug}_{key}": value for key, value in result.stats.items()}
            )
        return TransformResult(current, stats)
