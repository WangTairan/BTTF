"""Language-neutral contracts for deterministic source interferences."""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

SourceT = TypeVar("SourceT", str, bytes)


@dataclass(frozen=True)
class InterferenceContext:
    seed: int
    identity: str
    protected_names: tuple[str, ...] = ()

    def random(self, salt: str) -> random.Random:
        digest = hashlib.sha256(f"{self.seed}:{self.identity}:{salt}".encode()).digest()
        return random.Random(int.from_bytes(digest[:8]))


@dataclass(frozen=True)
class TransformResult(Generic[SourceT]):
    content: SourceT
    stats: dict[str, int]

    @property
    def source(self) -> SourceT:
        """Compatibility name used by the Python implementation."""
        return self.content


class Interference(ABC, Generic[SourceT]):
    """Contract implemented by every independently pluggable interference."""

    category: str
    slug: str
    description: str

    @abstractmethod
    def apply(
        self, source: SourceT, context: InterferenceContext
    ) -> TransformResult[SourceT]:
        """Return transformed source and integer operation statistics."""
