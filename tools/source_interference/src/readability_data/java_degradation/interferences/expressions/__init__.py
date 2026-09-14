"""Control-flow and expression-level interferences."""

from readability_data.java_degradation.interferences.expressions.conditions import (
    InvertConditions,
)
from readability_data.java_degradation.interferences.expressions.literals import (
    EncodeIntegerLiterals,
    EncodeLiterals,
)

__all__ = [
    "EncodeIntegerLiterals",
    "EncodeLiterals",
    "InvertConditions",
]
